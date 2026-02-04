
const fs = require('fs');
const path = "C:\\Users\\sahte\\Desktop\\CCAD Dashboard\\CCAD_Support_Bible\\js\\data-seed.js";

try {
    let content = fs.readFileSync(path, 'utf8');

    // Make variables global so we can access them after eval
    content = content.replace('const SEED_DATA =', 'global.SEED_DATA =');

    // We suspect EQUIPMENT_DATA is also there. 
    // If it's not found by replace, no harm done if we wrap access in try-catch.
    content = content.replace('const EQUIPMENT_DATA =', 'global.EQUIPMENT_DATA =');

    // Remove the function definitions at the end to prevent side effects or errors
    // We'll just cut off everything after the data definitions.
    // Heuristic: SEED_DATA usually comes first.
    // Let's just try to eval the whole thing. The functions won't execute unless called.
    // But they might reference DB which is missing.
    // So we'll mock DB and isDBReady.

    global.window = {};
    global.DB = { putMany: () => { }, count: () => { }, getAll: () => { } };
    global.isDBReady = () => false;

    eval(content);

    const output = {
        faqs: global.SEED_DATA ? global.SEED_DATA.faqs : [],
        troubleshooting: global.SEED_DATA ? global.SEED_DATA.troubleshooting : [],
        equipment: global.EQUIPMENT_DATA || []
    };

    fs.writeFileSync('full_data.json', JSON.stringify(output, null, 2), 'utf8');
    console.log(`Extraction Complete: ${output.faqs.length} FAQs, ${output.troubleshooting.length} TS, ${output.equipment.length} Equipment.`);

} catch (e) {
    console.error("Extraction Error:", e);
}

