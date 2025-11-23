import { compileFromFile } from "json-schema-to-typescript";
import * as fs from "fs/promises";

const options = {
  additionalProperties: false,
  enableConstEnums: false,
  inferStringEnumKeysFromValues: true,
};

const models_path = "../../ingestion-workflow-model-schemas/";

const files: string[] = [
  "IngestionWorkflowInput.json"
];

const outputFile = "model.ts";

async function generateTypes() {
  // Step 1: Clear the file or initialize it
  await fs.writeFile(outputFile, ""); // resets the file

  // Step 2: Append each generated TypeScript definition
  for (const filename of files) {
    const ts = await compileFromFile(`${models_path}/${filename}`, options);
    await fs.appendFile(outputFile, ts);
  }

  console.log("Type definitions generated.");
}

generateTypes().catch(console.error);
