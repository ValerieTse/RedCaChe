import assert from "node:assert/strict";
import { resolvePostOpenUrl } from "../src/components/postLinks.js";

assert.equal(
  resolvePostOpenUrl({
    source_url: "https://www.rednote.com/user/profile/me/note001",
    open_url: "https://www.rednote.com/user/profile/me/note001?xsec_token=abc",
  }),
  "https://www.rednote.com/user/profile/me/note001?xsec_token=abc",
);

assert.equal(
  resolvePostOpenUrl({
    source_url: "https://www.rednote.com/user/profile/me/note001",
    open_url: null,
  }),
  "https://www.rednote.com/user/profile/me/note001",
);

assert.equal(
  resolvePostOpenUrl({
    import_source: "rednote",
    source_url: "https://www.rednote.com/user/profile/me/note001",
    open_url: null,
    raw_payload_json: {
      observed_url_variants: [
        "https://www.rednote.com/user/profile/me/note001",
        "https://www.rednote.com/user/profile/me/note001?xsec_token=fresh&xsec_source=pc_collect",
      ],
    },
  }),
  "https://www.rednote.com/user/profile/me/note001?xsec_token=fresh&xsec_source=pc_collect",
);

assert.equal(
  resolvePostOpenUrl({
    import_source: "rednote",
    source_url: "https://www.rednote.com/user/profile/me/note001",
    open_url: null,
  }),
  "https://www.rednote.com/user/profile/me/note001",
);

assert.equal(
  resolvePostOpenUrl({
    import_source: "rednote",
    note_id: "note001",
    source_url: null,
    open_url: null,
  }),
  "https://www.rednote.com/explore/note001",
);
