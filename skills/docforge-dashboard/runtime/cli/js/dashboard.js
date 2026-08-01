#!/usr/bin/env node
"use strict";
/* Launcher: delegates to the docforge-dashboard runtime. */

const { main } = require("../../dashboard.js");

main().then((code) => process.exit(code));
