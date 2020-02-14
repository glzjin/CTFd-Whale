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

function ezAlert(args) {
    const modal = modalTpl.format(args.title, args.body);
    const obj = $(modal);

    if (typeof args.body === "string") {
        obj.find(".modal-body").append(`<p>${args.body}</p>`);
    } else {
        obj.find(".modal-body").append($(args.body));
    }

    const button = $(
        '<button type="button" class="btn btn-primary" data-dismiss="modal">{0}</button>'
            .format(args.button)
    );

    if (args.success) {
        $(button).click(function () {
            args.success();
        });
    }

    if (args.large) {
        obj.find(".modal-dialog").addClass("modal-lg");
    }

    obj.find(".modal-footer").append(button);
    $("main").append(obj);

    obj.modal("show");

    $(obj).on("hidden.bs.modal", function () {
        $(this).modal("dispose");
    });

    return obj;
}

function ezQuery(args) {
    const modal = modalTpl.format(args.title, args.body);
    const obj = $(modal);

    if (typeof args.body === "string") {
        obj.find(".modal-body").append(`<p>${args.body}</p>`);
    } else {
        obj.find(".modal-body").append($(args.body));
    }

    const yes = $('<button type="button" class="btn btn-primary" data-dismiss="modal">Yes</button>');
    const no = $('<button type="button" class="btn btn-danger" data-dismiss="modal">No</button>');

    obj.find(".modal-footer").append(no);
    obj.find(".modal-footer").append(yes);

    $("main").append(obj);

    $(obj).on("hidden.bs.modal", function () {
        $(this).modal("dispose");
    });

    $(yes).click(function () {
        args.success();
    });

    obj.modal("show");

    return obj;
}

$(".delete-container").click(function (e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to delete <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    var row = $(this)
        .parent()
        .parent();

    ezQuery({
        title: "Destroy Container",
        body: body,
        success: function () {
            CTFd.fetch("/plugins/ctfd-whale/admin/containers?user_id=" + user_id, {
                method: "DELETE",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json"
                }
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (response) {
                    if (response.success) {
                        row.remove();
                    }
                });
        }
    });
});

$(".renew-container").click(function (e) {
    e.preventDefault();
    var container_id = $(this).attr("container-id");
    var challenge_id = $(this).attr("challenge-id");
    var user_id = $(this).attr("user-id");

    var body = "<span>Are you sure you want to renew <strong>Container #{0}</strong>?</span>".format(
        htmlentities(container_id)
    );

    ezQuery({
        title: "Renew Container",
        body: body,
        success: function () {
            CTFd.fetch("/plugins/ctfd-whale/admin/containers?user_id=" + user_id + "&challenge_id=" + challenge_id, {
                method: "PATCH",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json"
                }
            })
                .then(function (response) {
                    return response.json();
                })
                .then(function (response) {
                    if (response.success) {
                        ezAlert({
                            title: "Success",
                            body: "This instance has been renewed!",
                            button: "OK"
                        });
                    }
                });
        }
    });
});