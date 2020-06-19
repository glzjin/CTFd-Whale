from __future__ import division  # Use floating point for math calculations

import random
import uuid
from datetime import datetime

from jinja2 import Template

from CTFd.models import db, Challenges


class WhaleConfig(db.Model):
    key = db.Column(db.String(length=128), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<WhaleConfig (0) {1}>".format(self.key, self.value)


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


class WhaleContainer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(None, db.ForeignKey("users.id"))
    challenge_id = db.Column(None, db.ForeignKey("challenges.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, default=1)
    uuid = db.Column(db.String(256))
    port = db.Column(db.Integer, nullable=True, default=0)
    flag = db.Column(db.String(128), nullable=False)

    # Relationships
    user = db.relationship("Users", foreign_keys="WhaleContainer.user_id", lazy="select")
    challenge = db.relationship(
        "DynamicDockerChallenge", foreign_keys="WhaleContainer.challenge_id", lazy="select"
    )

    @property
    def http_subdomain(self):
        from .utils.db import DBConfig
        return Template(DBConfig.get_config(
            'template_http_subdomain', '{{ container.uuid }}'
        )).render(container=self)

    def __init__(self, user_id, challenge_id, port):
        from .utils.db import DBConfig
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.start_time = datetime.now()
        self.renew_count = 0
        self.uuid = str(uuid.uuid4())
        self.port = port
        self.flag = Template(DBConfig.get_config(
            'template_chall_flag', '{{ "flag{"+uuid.uuid4()|string+"}" }}'
        )).render(container=self, uuid=uuid, random=random)

    @property
    def user_access(self):
        configs = {}
        for c in WhaleConfig.query.all():
            configs[str(c.key)] = str(c.value)
        access = ''
        if self.challenge.redirect_type == 'http':
            subdomain_host = configs.get("frp_http_domain_suffix", "").lstrip(".")
            access = f'http://{self.http_subdomain}.{subdomain_host}'
            if configs.get('frp_http_port', '80') != '80':
                access += ':' + configs.get('frp_http_port')
        elif self.challenge.redirect_type == 'direct':
            access = f'nc {configs.get("frp_direct_ip_address", "")} {self.port}'
        return access

    @property
    def frp_config(self):
        configs = {}
        for c in WhaleConfig.query.all():
            configs[str(c.key)] = str(c.value)
        if self.challenge.redirect_type == 'http':
            return f"""
[http_{str(self.user_id)}-{self.uuid}]
type = http
local_ip = {str(self.user_id)}-{self.uuid}
local_port = {self.challenge.redirect_port}
subdomain = {self.http_subdomain}
use_compression = true
"""
        elif self.challenge.redirect_type == 'direct':
            return f"""
[direct_{str(self.user_id)}-{self.uuid}]
type = tcp
local_ip = {str(self.user_id)}-{self.uuid}
local_port = {self.challenge.redirect_port}
remote_port = {self.port}
use_compression = true

[direct_{str(self.user_id)}-{self.uuid}_udp]
type = udp
local_ip = {str(self.user_id)}-{self.uuid}
local_port = {self.challenge.redirect_port}
remote_port = {self.port}
use_compression = true
"""

    def __repr__(self):
        return "<WhaleContainer ID:(0) {1} {2} {3} {4}>".format(self.id, self.user_id, self.challenge_id,
                                                                self.start_time, self.renew_count)
