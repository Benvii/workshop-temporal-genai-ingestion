import yargs from "yargs";
import { hideBin } from "yargs/helpers";

import { Worker, NativeConnection } from "@temporalio/worker";

import { TS_CONVERSION_HTML } from "./html_conversion_activity";

async function run() {

  const argv = await yargs(hideBin(process.argv))
    .option("workerDebugMode", { type: "boolean", default: false })
    .parse();

  console.info("Worker starting...");

  const connection = await NativeConnection.connect({
    address: "localhost:7233",
  });


  try {
    const worker = await Worker.create({
      connection,
      namespace: "workshop-ingestion",
      taskQueue: "TS_WORKER_TASK_QUEUE",
      activities: {
        TS_CONVERSION_HTML,
      },
      identity: "ts-worker-identity",
      debugMode: argv.workerDebugMode,
    });

    await worker.run();
  } finally {
    await connection.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
