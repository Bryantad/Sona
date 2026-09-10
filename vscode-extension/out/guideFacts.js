"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkedFactArguments = checkedFactArguments;
exports.requestCheckedFacts = requestCheckedFacts;
/** Bounded CLI transport only; Python owns verification and all explanation text. */
const child_process_1 = require("child_process");
const guideModel_1 = require("./guideModel");
function checkedFactArguments(kind, projectRoot, options, receipt) {
    if (!projectRoot || (kind === "proof" && !receipt))
        throw new Error("Select the intended project and receipt first.");
    const args = ["-P", "-m", "sona", "guide", kind];
    if (kind === "proof")
        args.push(receipt);
    args.push("--project-root", projectRoot, "--json");
    if (options.mode)
        args.push("--mode", options.mode);
    if (options.style)
        args.push("--style", options.style);
    return args;
}
function requestCheckedFacts(python, kind, projectRoot, options, receipt) {
    const args = checkedFactArguments(kind, projectRoot, options, receipt);
    const env = { ...process.env, PYTHONIOENCODING: "utf-8" };
    delete env.PYTHONPATH;
    return new Promise((resolve, reject) => {
        const child = (0, child_process_1.execFile)(python, args, {
            cwd: projectRoot, env, encoding: "utf8", windowsHide: true, shell: false,
            timeout: 30000, maxBuffer: 2 * 1024 * 1024
        }, (error, stdout) => {
            if (error && error.code !== 1) {
                reject(new Error("Sona Guide could not complete the checked-fact request. Check the selected Python runtime and its time/output limits."));
                return;
            }
            try {
                const response = JSON.parse(stdout);
                (0, guideModel_1.guideText)(response);
                if (response.status !== "unavailable" && (response.basis !== "provider-facts" || response.fact_kind !== kind)) {
                    throw new Error("Unexpected provider response");
                }
                resolve(response);
            }
            catch {
                reject(new Error("The selected Sona runtime did not return supported Guide facts. Update the runtime and retry."));
            }
        });
        child.stdin?.end();
    });
}
