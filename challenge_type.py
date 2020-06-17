from __future__ import division  # Use floating point for math calculations

import math

from flask import Blueprint

from CTFd.models import (
    db,
    Solves,
    Fails,
    Flags,
    Challenges,
    ChallengeFiles,
    Tags,
    Hints,
)
from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils import user as current_user
from CTFd.utils.modes import get_model
from CTFd.utils.uploads import delete_file
from CTFd.utils.user import get_ip
from .models import WhaleContainer


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

    @staticmethod
    def create(request):
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

    @staticmethod
    def read(challenge):
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
                "id": DynamicValueDockerChallenge.id,
                "name": DynamicValueDockerChallenge.name,
                "templates": DynamicValueDockerChallenge.templates,
                "scripts": DynamicValueDockerChallenge.scripts,
            },
        }
        return data

    @staticmethod
    def update(challenge, request):
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

        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
                .filter(
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
                .count()
        )

        # It is important that this calculation takes into account floats.
        # Hence this file uses from __future__ import division
        value = (
                        ((challenge.minimum - challenge.initial) / (challenge.decay ** 2))
                        * (solve_count ** 2)
                ) + challenge.initial

        value = math.ceil(value)

        if value < challenge.minimum:
            value = challenge.minimum

        challenge.value = value

        db.session.commit()
        return challenge

    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.

        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        DynamicDockerChallenge.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()

    @staticmethod
    def attempt(challenge, request):
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

    @staticmethod
    def solve(user, team, challenge, request):
        """
        This method is used to insert Solves into the database in order to mark a challenge as solved.

        :param team: The Team object from the database
        :param chal: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        chal = DynamicDockerChallenge.query.filter_by(id=challenge.id).first()
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        Model = get_model()

        solve = Solves(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(req=request),
            provided=submission,
        )
        db.session.add(solve)

        if chal.dynamic_score == 1:

            solve_count = (
                Solves.query.join(Model, Solves.account_id == Model.id).filter(
                    Solves.challenge_id == challenge.id,
                    Model.hidden == False,
                    Model.banned == False,
                ).count()
            )

            # We subtract -1 to allow the first solver to get max point value
            solve_count -= 1

            # It is important that this calculation takes into account floats.
            # Hence this file uses from __future__ import division
            value = chal.initial + \
                    ((solve_count / chal.decay) ** 2) * \
                    (chal.minimum - chal.initial)

            value = math.ceil(value)

            if value < chal.minimum:
                value = chal.minimum

            chal.value = value

        db.session.commit()
        db.session.close()

    @staticmethod
    def fail(user, team, challenge, request):
        """
        This method is used to insert Fails into the database in order to mark an answer incorrect.

        :param team: The Team object from the database
        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return:
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        wrong = Fails(
            user_id=user.id,
            team_id=team.id if team else None,
            challenge_id=challenge.id,
            ip=get_ip(request),
            provided=submission,
        )
        db.session.add(wrong)
        db.session.commit()
        db.session.close()


class DynamicDockerChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "dynamic_docker"}
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)

    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)
    memory_limit = db.Column(db.Text, default="128m")
    cpu_limit = db.Column(db.Float, default=0.5)
    dynamic_score = db.Column(db.Integer, default=0)

    docker_image = db.Column(db.Text, default=0)
    redirect_type = db.Column(db.Text, default=0)
    redirect_port = db.Column(db.Integer, default=0)

    def __init__(self, *args, **kwargs):
        super(DynamicDockerChallenge, self).__init__(**kwargs)
        self.initial = kwargs["value"]
