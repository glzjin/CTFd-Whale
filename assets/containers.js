const $ = CTFd.lib.$;

function htmlentities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const modalTpl =
    '<div class="modal fade" tabindex="-1" role="dialog">' +
    '  <div class="modal-dialog" role="document">' +
    '    <div class="modal-content">' +
    '      <div class="modal-header">' +
    '        <h5 class="modal-title">{0}</h5>' +
    '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
    '          <span aria-hidden="true">&times;</span>' +
    "        </button>" +
    "      </div>" +
    '      <div class="modal-body">' +
    "      </div>" +
    '      <div class="modal-footer">' +
    "      </div>" +
    "    </div>" +
    "  </div>" +
    "</div>";

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