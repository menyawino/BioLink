import postgres from 'postgres';

const sql = postgres('postgres://biolink:biolink_secret@localhost:5432/biolink');

async function test() {
  try {
    const r = await sql`SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'`;
    console.log('Tables:', r.map(t => t.table_name));
    await sql.end();
  } catch (e: any) {
    console.error('Error:', e.message);
    process.exit(1);
  }
}

test();
