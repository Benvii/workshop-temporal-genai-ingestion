import {Source, StageEnum,} from "./model";

import * as path from "path";
import * as fs from "fs/promises";

import { Context } from '@temporalio/activity';
import {JSDOM} from "jsdom";
import Defuddle from "defuddle";

import TurndownService from "turndown";
import {Readability} from "@slax-lab/readability";


export async function TS_CONVERSION_HTML(
  source: Source,
): Promise<Source> {
  console.log("Web conversion activity started for source %s", source.uri);

  const root_git_dir = path.join(__dirname, "..", "..");
  const workflowId = Context.current().info.workflowExecution.workflowId;

  // Create workflow conversion output folder
  const artifactsDir = path.join(
      root_git_dir,
    "temporal_workdir", // On doit pouvoir s'en passer via var d'env + workflow ID depuis le context
    workflowId,
    "conversion"
  );
  await fs.mkdir(artifactsDir, { recursive: true });


  // Création du dossier où sera stocké le résultat s'il n'existe pas
  // temporal_workdir/{workflow-uuid}/conversion/original_filename.md
  if (source.raw_file_path == null) {
    source.error = "Can't convert source as source.raw_file_path is empty";
    return source;
  }

  const source_raw_file_path = path.join(root_git_dir, source.raw_file_path);
  const rawFileName = path.basename(source_raw_file_path);
  const outputFilePath = path.join(artifactsDir, rawFileName + ".md");

  let markdown = "";

  // COMPLETER ICI - START - Partie 3
  // - lire le fichier HTML : source_raw_file_path
  // - suivre les indications partie 3, init Defuddle + parsing
  // - chainer TurnItDown pour la conversion en Markdown celle de Defuddle ne fonctionnant pas
  // - peupler la metadata['title'] avec le titre extrait pas Defuddle
  // - écrire le markdown dans markdown, la suite de squelette l'enregistre au bon endroit
  // COMPLETER ICI - END - Partie 3


    // Save converted markdown content
    await fs.writeFile(outputFilePath, markdown, { encoding: "utf-8" });
    console.log("Saved converted markdown to %s", outputFilePath);

    source.current_stage = StageEnum.CONVERTION;
    source.converted_md_path = outputFilePath;


  return source;
}
