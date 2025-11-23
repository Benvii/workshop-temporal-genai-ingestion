import {Source, StageEnum,} from "./model";

import * as path from "path";
import * as fs from "fs/promises";

import { Context } from '@temporalio/activity';
import {JSDOM} from "jsdom";
import Defuddle from "defuddle";

import TurndownService from "turndown";


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

  // COMPLETER ICI - START - Partie 3
  // - lire le fichier HTML : source_raw_file_path
  // - suivre les indications partie 3, init Defuddle + parsing
  // - chainer TurnItDown pour la conversion en Markdown celle de Defuddle ne fonctionnant pas
  // - peupler la metadata['title'] avec le titre extrait pas Defuddle
  // - écrire le markdown dans markdown, la suite de squelette l'enregistre au bon endroit
  const html_source = await fs.readFile(source_raw_file_path, { encoding: "utf-8" });
  const jsdom = new JSDOM(html_source, { url: source.uri, pretendToBeVisual: true });
  const window = jsdom.window;
  const document = window.document;

  const defuddle = new Defuddle(document);
  const article = defuddle.parse();

  const turndownService = new TurndownService();
  const markdown = turndownService.turndown(article.content);

  // Peupler les metadonnées.
  source.metadata ??= {}; // S'assure que source.metadata est initialisé
  source.metadata['title'] = article.title;
  console.log("Extracted title %s", article);
  // COMPLETER ICI - END - Partie 3


  // Save converted markdown content
  await fs.writeFile(outputFilePath, markdown, { encoding: "utf-8" });
  console.log("Saved converted markdown to %s", outputFilePath);

  source.current_stage = StageEnum.CONVERTION;
  source.converted_md_path = outputFilePath;

  return source;
}
