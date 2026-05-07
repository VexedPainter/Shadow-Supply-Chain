const http = require('http');

async function test() {
    try {
        console.log("1. Logging in...");
        const loginRes = await fetch("http://127.0.0.1:8000/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "admin", password: "nexus2026" })
        });
        const loginData = await loginRes.json();
        const cookie = loginRes.headers.get('set-cookie');
        
        console.log("\n2. Testing Exact Match Intercept (SKU: HP-XL-001)...");
        const req2 = await fetch("http://127.0.0.1:8000/api/emergency-purchase/verify", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Cookie": cookie
            },
            body: JSON.stringify({
                part_name: "Hydro-Pump XL",
                sku: "HP-XL-001",
                quantity: 1,
                department: "Maintenance",
                employee: "Test User"
            })
        });
        const res2 = await req2.json();
        console.log("Response (Exact Match Test):", res2);
        
        console.log("\nTests Complete.");
    } catch(e) {
        console.error(e);
    }
}

test();
