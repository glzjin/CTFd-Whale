window.challenge.data = undefined;

window.challenge.renderer = new markdownit({
    html: true,
    linkify: true,
});

window.challenge.preRender = function () {

};

window.challenge.render = function (markdown) {
    return window.challenge.renderer.render(markdown);
};


window.challenge.postRender = function () {
    loadInfo();
};

function loadInfo () {
    var challenge_id = parseInt($('#challenge-id').val());
    var url = "/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    var params = {
    };

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if(response.remaining_time === undefined) {
            $('#whale-panel').html('<div class="card" style="width: 100%;">' +
                  '<div class="card-body">' +
                    '<h5 class="card-title">Instance Info</h5>' +
                    '<button type="button" class="btn btn-primary card-link" id="whale-button-boot" onclick="window.challenge.boot()">Launch an instance</button>' +
                  '</div>' +
                '</div>');
        } else {
            if(response.type === 'http') {
                $('#whale-panel').html('<div class="card" style="width: 100%;">' +
                  '<div class="card-body">' +
                    '<h5 class="card-title">Instance Info</h5>' +
                    '<h6 class="card-subtitle mb-2 text-muted" id="whale-challenge-count-down">Remaining Time：' + response.remaining_time + 's</h6>' +
                    '<p class="card-text">http://' + response.domain + '</p>' +
                    '<button type="button" class="btn btn-danger card-link" id="whale-button-destroy" onclick="window.challenge.destroy()">Destroy this instance</button>' +
                    '<button type="button" class="btn btn-success card-link" id="whale-button-renew" onclick="window.challenge.renew()">Renew this instance</button>' +
                  '</div>' +
                '</div>');
            } else {
                $('#whale-panel').html('<div class="card" style="width: 100%;">' +
                  '<div class="card-body">' +
                    '<h5 class="card-title">Instance Info</h5>' +
                    '<h6 class="card-subtitle mb-2 text-muted" id="whale-challenge-count-down">Remaining Time：' + response.remaining_time + 's</h6>' +
                    '<p class="card-text">' + response.ip + ':' + response.port + '</p>' +
                    '<button type="button" class="btn btn-danger card-link" id="whale-button-destroy" onclick="window.challenge.destroy()">Destroy this instance</button>' +
                    '<button type="button" class="btn btn-success card-link" id="whale-button-renew" onclick="window.challenge.renew()">Renew this instance</button>' +
                  '</div>' +
                '</div>');
            }

            if(window.t !== undefined) {
                clearInterval(window.t);
                window.t = undefined;
            }

            function showAuto(){
                const origin = $('#whale-challenge-count-down')[0].innerHTML;
                const second = parseInt(origin.split("：")[1].split('s')[0]) - 1;
                $('#whale-challenge-count-down')[0].innerHTML = 'Remaining Time：' + second + 's';
                if(second < 0) {
                    loadInfo();
                }
            }

            window.t = setInterval(showAuto, 1000);
        }
    });
};

window.challenge.destroy = function() {
    var challenge_id = parseInt($('#challenge-id').val());
    var url = "/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    $('#whale-button-destroy')[0].innerHTML = "Waiting...";
    $('#whale-button-destroy')[0].disabled = true;

    var params = {
    };

    CTFd.fetch(url, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if(response.success) {
            loadInfo();
            ezal({
                title: "Success",
                body: "Your instance has been destroyed!",
                button: "OK"
            });
        } else {
            $('#whale-button-destroy')[0].innerHTML = "Destroy this instance";
            $('#whale-button-destroy')[0].disabled = false;
            ezal({
                title: "Fail",
                body: response.msg,
                button: "OK"
            });
        }
    });
};

window.challenge.renew = function() {
    var challenge_id = parseInt($('#challenge-id').val());
    var url = "/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    $('#whale-button-renew')[0].innerHTML = "Waiting...";
    $('#whale-button-renew')[0].disabled = true;

    var params = {
    };

    CTFd.fetch(url, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if(response.success) {
            loadInfo();
            ezal({
                title: "Success",
                body: "Your instance has been renewed!",
                button: "OK"
            });
        } else {
            $('#whale-button-renew')[0].innerHTML = "Renew this instance";
            $('#whale-button-renew')[0].disabled = false;
            ezal({
                title: "Fail",
                body: response.msg,
                button: "OK"
            });
        }
    });
};

window.challenge.boot = function () {
    var challenge_id = parseInt($('#challenge-id').val());
    var url = "/plugins/ctfd-whale/container?challenge_id=" + challenge_id;

    $('#whale-button-boot')[0].innerHTML = "Waiting...";
    $('#whale-button-boot')[0].disabled = true;

    var params = {
    };

    CTFd.fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if(response.success) {
            loadInfo();
            ezal({
                title: "Success",
                body: "Your instance has been deployed!",
                button: "OK"
            });
        } else {
            $('#whale-button-boot')[0].innerHTML = "Launch an instance";
            $('#whale-button-boot')[0].disabled = false;
            ezal({
                title: "Fail",
                body: response.msg,
                button: "OK"
            });
        }
    });
};


window.challenge.submit = function (cb, preview) {
    var challenge_id = parseInt($('#challenge-id').val());
    var submission = $('#submission-input').val();
    var url = "/api/v1/challenges/attempt";

    if (preview) {
        url += "?preview=true";
    }

    var params = {
        'challenge_id': challenge_id,
        'submission': submission
    };

    CTFd.fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        cb(response);
    });
};