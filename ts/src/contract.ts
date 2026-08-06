/**
 * Reading the contracts — for **typing only**.
 *
 * The contracts are the normative SSOT (D §6), so both implementations read the
 * same authored documents. Building the TypeScript profile from a Python-emitted
 * artifact would give the base contract a Python-privileged reading, which is
 * the arrangement a parity obligation exists to prevent.
 *
 * **What this side deliberately does not do**, because D §9 scopes `ts/` to the
 * shared-encoding path and formal model limitation 9 records M10 as the only
 * cross-implementation row:
 *
 * * no **contract content identity** and no **compiled profile identity** — §8
 *   sites compilation as Python-only, since it is not a shared encoding;
 * * no **succession validation**;
 * * no **retirement** semantics.
 *
 * The last two are not skipped, they are **refused**. A contract declaring a
 * predecessor, or carrying a retired declaration, is rejected with
 * `UncheckableContract`. Parsing past them would make this a second, weaker
 * reading of the normative source — which is worse than not reading it, because
 * it would look like agreement.
 */

import { parse as parseYaml } from "yaml";
import { MalformedContract, UncheckableContract } from "./errors.js";

const TAG_ENCODING = "science.identity.v1";
const NAME = /^[a-z][a-z0-9-]*$/;

export interface ClaimGrammar {
  readonly version: number;
  readonly quantifiers: readonly string[];
  readonly polarities: readonly string[];
  readonly signInaptTag: string;
  readonly layers: readonly string[];
}

export interface BaseContract {
  readonly name: string;
  readonly version: number;
  readonly claimGrammar: ClaimGrammar;
}

export interface SortDecl {
  readonly name: string;
}

export interface DimensionDecl {
  readonly name: string;
  readonly restrictionSort: string;
}

export interface OperatorDecl {
  readonly name: string;
  readonly arity: number;
  readonly argSorts: readonly string[];
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly dimensions: readonly string[];
}

export interface DomainContract {
  readonly namespace: string;
  readonly version: number;
  readonly sorts: ReadonlyMap<string, SortDecl>;
  readonly dimensions: ReadonlyMap<string, DimensionDecl>;
  readonly operators: ReadonlyMap<string, OperatorDecl>;
}

function mapping(value: unknown, where: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new MalformedContract(`${where}: expected a mapping, found ${JSON.stringify(value)}`);
  }
  return value as Record<string, unknown>;
}

function exactFields(value: Record<string, unknown>, required: string[], optional: string[], where: string): void {
  const permitted = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    // D5: an unrecognized field is refused at load, never ignored — a contract
    // quietly accepting one would make the reader and the loader disagree about
    // what the document says.
    if (!permitted.has(key)) throw new MalformedContract(`${where}: unknown field ${JSON.stringify(key)}`);
  }
  for (const key of required) {
    if (!(key in value)) throw new MalformedContract(`${where}: missing field ${JSON.stringify(key)}`);
  }
}

function positiveInt(value: unknown, where: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 1) {
    throw new MalformedContract(`${where}: expected a positive integer, found ${JSON.stringify(value)}`);
  }
  return value;
}

function tag(value: unknown, where: string): string {
  if (typeof value !== "string" || !NAME.test(value)) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a tag; expected \`[a-z][a-z0-9-]*\``);
  }
  return value;
}

function closedSet(value: unknown, where: string): string[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new MalformedContract(`${where}: expected a non-empty list`);
  }
  const tags = value.map((entry, index) => tag(entry, `${where}[${index}]`));
  if (new Set(tags).size !== tags.length) throw new MalformedContract(`${where}: duplicate tag in a closed set`);
  return tags;
}

export function parseBaseContract(text: string, source: string): BaseContract {
  const document = mapping(parseYaml(text), source);
  exactFields(document, ["contract", "version", "claim_grammar"], [], source);
  if (document.contract !== "science") {
    throw new MalformedContract(
      `${source}: the base contract is named \`science\`, found ${JSON.stringify(document.contract)}`,
    );
  }
  const grammarDocument = mapping(document.claim_grammar, `${source}.claim_grammar`);
  exactFields(
    grammarDocument,
    ["version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"],
    [],
    `${source}.claim_grammar`,
  );
  if (grammarDocument.tag_encoding !== TAG_ENCODING) {
    throw new MalformedContract(
      `${source}.claim_grammar.tag_encoding: this implementation carries ${TAG_ENCODING}, ` +
        `the contract names ${JSON.stringify(grammarDocument.tag_encoding)}`,
    );
  }
  const polarities = closedSet(grammarDocument.polarities, `${source}.claim_grammar.polarities`);
  const signInaptTag = tag(grammarDocument.sign_inapt_tag, `${source}.claim_grammar.sign_inapt_tag`);
  if (polarities.includes(signInaptTag)) {
    // §7.5: `inapt` and `unsigned` are different facts, and a projection that
    // cannot tell them apart has lost the distinction it exists to carry.
    throw new MalformedContract(
      `${source}.claim_grammar.sign_inapt_tag: ${JSON.stringify(signInaptTag)} is also an assertable polarity`,
    );
  }
  return {
    name: "science",
    version: positiveInt(document.version, `${source}.version`),
    claimGrammar: {
      version: positiveInt(grammarDocument.version, `${source}.claim_grammar.version`),
      quantifiers: closedSet(grammarDocument.quantifiers, `${source}.claim_grammar.quantifiers`),
      polarities,
      signInaptTag,
      layers: closedSet(grammarDocument.layers, `${source}.claim_grammar.layers`),
    },
  };
}

function refuseRetired(body: Record<string, unknown>, where: string): void {
  if ("retired" in body) {
    throw new UncheckableContract(
      `${where}: retirement is an authoring-boundary property (§7.3a) and this implementation carries the shared-encoding path only. It refuses rather than reading past a rule it cannot enforce.`,
    );
  }
}

function declarations(value: unknown, where: string): Record<string, unknown> {
  return value === undefined ? {} : mapping(value, where);
}

export function parseDomainContract(text: string, source: string, base: BaseContract): DomainContract {
  const document = mapping(parseYaml(text), source);
  exactFields(document, ["contract", "version", "lineage"], ["sorts", "dimensions", "operators"], source);

  if (document.lineage !== "genesis") {
    throw new UncheckableContract(
      `${source}.lineage: succession is validated against a declared predecessor (§8.3), which this implementation does not carry. Only a genesis contract is readable here.`,
    );
  }
  const namespace = tag(document.contract, `${source}.contract`);

  const sorts = new Map<string, SortDecl>();
  for (const [name, body] of Object.entries(declarations(document.sorts, `${source}.sorts`))) {
    const where = `${source}.sorts.${name}`;
    const sortBody = mapping(body, where);
    exactFields(sortBody, ["vocabulary"], ["retired"], where);
    refuseRetired(sortBody, where);
    sorts.set(tag(name, where), { name });
  }

  const dimensions = new Map<string, DimensionDecl>();
  for (const [name, body] of Object.entries(declarations(document.dimensions, `${source}.dimensions`))) {
    const where = `${source}.dimensions.${name}`;
    const dimensionBody = mapping(body, where);
    exactFields(dimensionBody, ["restriction_sort"], ["retired"], where);
    refuseRetired(dimensionBody, where);
    const restrictionSort = tag(dimensionBody.restriction_sort, `${where}.restriction_sort`);
    if (!sorts.has(restrictionSort)) {
      throw new MalformedContract(
        `${where}.restriction_sort: ${JSON.stringify(restrictionSort)} is not a declared sort`,
      );
    }
    dimensions.set(tag(name, where), { name, restrictionSort });
  }

  const operators = new Map<string, OperatorDecl>();
  for (const [name, body] of Object.entries(declarations(document.operators, `${source}.operators`))) {
    const where = `${source}.operators.${name}`;
    const operatorBody = mapping(body, where);
    exactFields(
      operatorBody,
      ["arity", "arg_sorts", "sign_apt", "layers", "dimensions"],
      ["description", "retired"],
      where,
    );
    refuseRetired(operatorBody, where);
    const arity = positiveInt(operatorBody.arity, `${where}.arity`);
    if (!Array.isArray(operatorBody.arg_sorts) || operatorBody.arg_sorts.length !== arity) {
      // Every slot of Fin(arity(op)) is filled, and no slot twice (§6.2).
      throw new MalformedContract(`${where}.arg_sorts: expected exactly ${arity} sorts, one per slot`);
    }
    const argSorts = operatorBody.arg_sorts.map((entry, index) => tag(entry, `${where}.arg_sorts[${index}]`));
    for (const sort of argSorts) {
      if (!sorts.has(sort))
        throw new MalformedContract(`${where}.arg_sorts: ${JSON.stringify(sort)} is not a declared sort`);
    }
    if (typeof operatorBody.sign_apt !== "boolean") {
      throw new MalformedContract(`${where}.sign_apt: expected true or false`);
    }
    const layers = closedSet(operatorBody.layers, `${where}.layers`);
    for (const layer of layers) {
      if (!base.claimGrammar.layers.includes(layer)) {
        throw new MalformedContract(
          `${where}.layers: ${JSON.stringify(layer)} is not a layer the base contract declares`,
        );
      }
    }
    if (!Array.isArray(operatorBody.dimensions)) throw new MalformedContract(`${where}.dimensions: expected a list`);
    const permitted = operatorBody.dimensions.map((entry, index) => tag(entry, `${where}.dimensions[${index}]`));
    for (const dimension of permitted) {
      if (!dimensions.has(dimension)) {
        throw new MalformedContract(`${where}.dimensions: ${JSON.stringify(dimension)} is not a declared dimension`);
      }
    }
    operators.set(tag(name, where), {
      name,
      arity,
      argSorts,
      signApt: operatorBody.sign_apt,
      layers,
      dimensions: permitted,
    });
  }

  return { namespace, version: positiveInt(document.version, `${source}.version`), sorts, dimensions, operators };
}
