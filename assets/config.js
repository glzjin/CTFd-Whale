const $ = CTFd.lib.$;

async function updateConfigs(event) {
    event.preventDefault();
    const obj = $(this).serializeJSON();
    const params = {};

    Object.keys(obj).forEach(function (x) {
        if (obj[x] === "true") {
            params[x] = true;
        } else if (obj[x] === "false") {
            params[x] = false;
        } else {
            params[x] = obj[x];
        }
    });

    await CTFd.api.patch_config_list({}, params);
    location.reload();
}

$(".config-section > form:not(.form-upload)").submit(updateConfigs);