from flask import Blueprint

from CTFd.models import (
    db,
    Flags,
)
from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.dynamic_challenges import DynamicValueChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils import user as current_user
from .models import WhaleContainer, DynamicDockerChallenge
from .utils.control import ControlUtil


class DynamicValueDockerChallenge(BaseChallenge):
    id = "dynamic_docker"  # Unique identifier used to register challenges
    name = "dynamic_docker"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/ctfd-whale/assets/create.html",
        "update": "/plugins/ctfd-whale/assets/update.html",
        "view": "/plugins/ctfd-whale/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/ctfd-whale/assets/create.js",
        "update": "/plugins/ctfd-whale/assets/update.js",
        "view": "/plugins/ctfd-whale/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/ctfd-whale/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "ctfd-whale-challenge",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )

    @classmethod
    def create(cls, request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        challenge = DynamicDockerChallenge(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = DynamicDockerChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        if challenge.dynamic_score == 1:
            return DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()
        return challenge

    @classmethod
    def attempt(cls, challenge, request):
        """
        This method is used to check whether a given input is right or wrong. It does not make any changes and should
        return a boolean for correctness and a string to be shown to the user. It is also in charge of parsing the
        user's input from the request itself.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()

        if len(flags) > 0:
            for flag in flags:
                if get_flag_class(flag.type).compare(flag, submission):
                    return True, "Correct"
            return False, "Incorrect"
        else:
            user_id = current_user.get_current_user().id
            q = db.session.query(WhaleContainer)
            q = q.filter(WhaleContainer.user_id == user_id)
            q = q.filter(WhaleContainer.challenge_id == challenge.id)
            records = q.all()
            if len(records) == 0:
                return False, "Please solve it during the container is running"

            container = records[0]
            if container.flag == submission:
                return True, "Correct"
            return False, "Incorrect"

    @classmethod
    def solve(cls, user, team, challenge, request):
        """
        This method is used to insert Solves into the database in order to mark a challenge as solved.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        super().solve(user, team, challenge, request)

        if challenge.dynamic_score == 1:
            DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()
        db.session.close()

    @classmethod
    def delete(cls, challenge):
        DynamicDockerChallenge.query.filter_by(
            id=challenge.id
        ).delete()
        for container in WhaleContainer.query.filter_by(
            challenge_id=challenge.id
        ).all():
            ControlUtil.try_remove_container(container.user_id)
        super().delete(challenge)
