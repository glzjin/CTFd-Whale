const $ = CTFd.lib.$;

function htmlentities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

$(".delete-container").click(function(e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to delete <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    var row = $(this)
        .parent()
        .parent();

    CTFd.ui.ezq.ezQuery({
        title: "Destroy Container",
        body: body,
        success: function() {
            CTFd.fetch("/plugins/ctfd-whale/admin/containers?user_id=" + user_id, {
                    method: "DELETE",
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json"
                    }
                })
                .then(function(response) {
                    return response.json();
                })
                .then(function(response) {
                    if (response.success) {
                        row.remove();
                    }
                });
        }
    });
});

$(".renew-container").click(function(e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var challenge_id = $(this).attr("challenge-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to renew <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    CTFd.ui.ezq.ezQuery({
        title: "Renew Container",
        body: body,
        success: function() {
            CTFd.fetch("/plugins/ctfd-whale/admin/containers?user_id=" + user_id + "&challenge_id=" + challenge_id, {
                    method: "PATCH",
                    credentials: "same-origin",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json"
                    }
                })
                .then(function(response) {
                    return response.json();
                })
                .then(function(response) {
                    if (response.success) {
                        CTFd.ui.ezq.ezAlert({
                            title: "Success",
                            body: "This instance has been renewed!",
                            button: "OK"
                        });
                    }
                });
        }
    });
});