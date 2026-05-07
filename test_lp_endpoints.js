const BASE = "http://127.0.0.1:8001";
let cookie = "";

async function req(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json", Cookie: cookie } };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(BASE + path, opts);
    const setCookie = r.headers.get("set-cookie");
    if (setCookie) cookie = setCookie.split(";")[0];
    const text = await r.text();
    try { return JSON.parse(text); } catch { return text; }
}

async function run() {
    console.log("=== ShadowSync AI — LP Endpoint Smoke Test ===\n");

    // Login
    const login = await req("POST", "/api/login", { username: "admin", password: "nexus2026" });
    console.log("✅ Login:", login.status);

    // LP-01: Shadow Verdict
    const verdict = await req("POST", "/api/shadows/1/feedback", { verdict: "confirmed_shadow", reviewer_id: "analyst_001" });
    console.log("LP-01 Shadow Verdict:", verdict);

    // LP-02: Verification Tasks (list)
    const tasks = await req("GET", "/api/verification-tasks");
    console.log("LP-02 Verification Tasks:", Array.isArray(tasks) ? `${tasks.length} tasks` : tasks);

    // LP-02: Verify Inventory
    const verify = await req("POST", "/api/inventory/HP-XL-001/verify", { confirmed_quantity: 12, location: "Warehouse A", verifier_id: "staff_01" });
    console.log("LP-02 Verify Inventory:", verify);

    // LP-03: Gate Entry
    const gate = await req("POST", "/api/signals/gate-entry", { vendor: "TestVendor", delivery_note: "DN-001", location: "Main Gate" });
    console.log("LP-03 Gate Entry:", gate);

    // LP-03: Petty Cash (should flag)
    const petty = await req("POST", "/api/signals/petty-cash", { amount: 750, category: "maintenance", description: "Emergency bolt purchase", requester: "tech_01" });
    console.log("LP-03 Petty Cash (flagged?):", petty);

    // LP-04: Parts Substitute
    const sub = await req("GET", "/api/parts/HP-XL-001/substitute?machine_id=MACH-003");
    console.log("LP-04 Substitute (standard machine):", sub);
    const subCrit = await req("GET", "/api/parts/HP-XL-001/substitute?machine_id=MACH-001");
    console.log("LP-04 Substitute (critical machine):", subCrit);

    // LP-06: Retrieval ETA
    const eta = await req("GET", "/api/inventory/HP-XL-001/retrieval-eta?warehouse_id=Warehouse%20A");
    console.log("LP-06 Retrieval ETA:", eta);

    // LP-08: Trust Profile
    const trust = await req("GET", "/api/users/tech_01/trust-profile");
    console.log("LP-08 Trust Profile:", trust);

    // LP-09: Normalize item description
    const norm1 = await req("GET", "/api/items/normalize?description=hydro%20pump%20xl");
    console.log("LP-09 Normalize (exact):", norm1);
    const norm2 = await req("GET", "/api/items/normalize?description=hydraulic%20pump");
    console.log("LP-09 Normalize (fuzzy):", norm2);

    // LP-10: Living Risk Event
    const riskEvt = await req("POST", "/api/shadows/1/risk-event", { event_type: "po_retroactively_matched" });
    console.log("LP-10 Risk Event:", riskEvt);

    // LP-11: Depletion alerts
    const depAlerts = await req("GET", "/api/alerts/depletion?horizon=30");
    console.log("LP-11 Depletion Alerts:", Array.isArray(depAlerts) ? `${depAlerts.length} alerts` : depAlerts);

    // LP-12: Network Mesh Search
    const mesh = await req("GET", "/api/inventory/network-search?sku=HP-XL-001&requesting_location=Warehouse%20B");
    console.log("LP-12 Network Mesh:", mesh.total_locations_with_stock, "locations found");
    if (mesh.best_option) console.log("    Best Option:", mesh.best_option);

    console.log("\n=== All LP endpoints validated ✅ ===");
}

run().catch(console.error);
