/**
 * `Claim` — the typed claim, and the only route to one, on this side too.
 *
 * M13's requirement is that a `Claim` is opaque and reachable only through a
 * validated construction, so that the profile-dependent checks happen **once**
 * and no downstream reader re-validates. That requirement is not Python's; it is
 * the claim's. A TypeScript path that accepted an object literal shaped like a
 * claim, or cast the fixture's components straight to `Claim`, would exercise
 * the encoding and skip the constructor — and the parity run would then be
 * comparing two different four-stage paths, one of them three stages long.
 *
 * `private constructor` states the rule to the compiler and enforces nothing at
 * run time, which is the wrong half for the same reason `typing.final` was on
 * the Python side. The mint token below is the enforcement.
 */

import {
  ArgumentSortMismatch,
  ArityMismatch,
  ClaimError,
  InadmissibleLayer,
  MalformedReferent,
  PolarityRefused,
  RestrictionSortMismatch,
  UndeclaredDimension,
  UnknownQuantifier,
  UntypedQualifier,
  UntypedReferent,
} from "./errors.js";
import { type ProfileSpec, resolveOperator } from "./profile.js";

const MINT = Symbol("science.claim.mint");

/**
 * A bound referent: a term identifier together with the sort it came from.
 *
 * `term` is the one position in a claim that nothing downstream checks — every
 * other identifier is matched against the profile's tables, and a referent's
 * term is checked only for membership, which is decode's against a snapshot. So
 * the field invariant lives here.
 */
export class Referent {
  readonly sort: string;
  readonly term: string;

  constructor(sort: string, term: string) {
    requireIdentifier(sort, "a referent's sort");
    requireIdentifier(term, "a referent's term");
    this.sort = sort;
    this.term = term;
    Object.freeze(this);
  }
}

/** One entry of the flat fragment: `d ↦ ⟨quantifier, restriction⟩` (§6.4). */
export class Qualifier {
  readonly quantifier: string;
  readonly restriction: Referent;

  constructor(quantifier: string, restriction: Referent) {
    if (!(restriction instanceof Referent)) {
      throw new UntypedReferent("a qualifier's restriction is not a Referent; a bare term carries no sort to check");
    }
    this.quantifier = quantifier;
    this.restriction = restriction;
    Object.freeze(this);
  }
}

export interface ClaimParts {
  readonly operator: string;
  readonly args: readonly Referent[];
  readonly qualifiers: ReadonlyMap<string, Qualifier>;
  /** `null` when the operator has no sign to assert — `Polarity(op)` is then the unit type (§6.3). */
  readonly polarity: string | null;
  readonly layer: string;
}

export class Claim {
  readonly operator: string;
  readonly args: readonly Referent[];
  readonly qualifiers: ReadonlyMap<string, Qualifier>;
  /** Always a tag, and the base contract's `sign_inapt_tag` where the operator has no sign (§7.5). */
  readonly polarity: string;
  readonly layer: string;

  constructor(token: symbol, parts: ClaimParts & { polarity: string }) {
    if (token !== MINT) {
      throw new ClaimError(
        "Claim is validated at construction — use buildClaim(profile, parts). A field-wise constructor " +
          "would put an unchecked claim downstream of the one boundary that checks (M13), and every reader " +
          "that trusts a Claim unconditionally would then be wrong.",
      );
    }
    this.operator = parts.operator;
    this.args = Object.freeze([...parts.args]);
    this.qualifiers = new Map(parts.qualifiers);
    this.polarity = parts.polarity;
    this.layer = parts.layer;
    Object.freeze(this);
  }
}

function requireIdentifier(value: unknown, where: string): void {
  if (typeof value !== "string" || value === "") {
    throw new MalformedReferent(
      `${where} is ${JSON.stringify(value)}, not a term identifier. Every position in π_claim is an identifier (§6.5), and a referent's fields are the only ones no downstream check would catch.`,
    );
  }
}

/**
 * The validated constructor. Every check here is profile-dependent, and each one
 * refuses distinctly — M11 decodes each ill-formed input in turn.
 *
 * Retirement is **not** among them: §7.3a puts it in authoring, and this
 * implementation refuses a contract carrying a retired declaration outright
 * rather than half-enforcing an authoring boundary it does not own.
 */
export function buildClaim(profile: ProfileSpec, parts: ClaimParts): Claim {
  const declaration = resolveOperator(profile, parts.operator);

  if (parts.args.length !== declaration.arity) {
    throw new ArityMismatch(
      `${parts.operator} has arity ${declaration.arity}; ${parts.args.length} argument(s) supplied. Every slot of Fin(arity(op)) is filled, and no slot is filled twice.`,
    );
  }
  parts.args.forEach((referent, index) => {
    if (!(referent instanceof Referent)) {
      throw new UntypedReferent(
        `slot ${index} of ${parts.operator} does not hold a Referent. A slot is typed Referent(s) (§6.2), and a bare term carries no sort to check against the one declared.`,
      );
    }
    if (referent.sort !== declaration.argSorts[index]) {
      throw new ArgumentSortMismatch(
        `slot ${index} of ${parts.operator} is declared ${declaration.argSorts[index]}; ${referent.term} is of sort ${referent.sort}. Inside the model these are different types, so this is not a rejected value but a term with no slot to occupy.`,
      );
    }
  });

  const permitted = new Set(declaration.dimensions);
  for (const [dimension, qualifier] of parts.qualifiers) {
    if (!(qualifier instanceof Qualifier)) {
      throw new UntypedQualifier(
        `the qualifier on ${dimension} is not a Qualifier. Structural typing is not enough: any object exposing \`quantifier\` and \`restriction\` would otherwise be stored inside a Claim and trusted as one.`,
      );
    }
    if (!permitted.has(dimension)) {
      throw new UndeclaredDimension(
        `${parts.operator} does not permit dimension ${dimension}; Dims(op) is declared per operator (§6.2).`,
      );
    }
    if (!profile.claimGrammar.quantifiers.includes(qualifier.quantifier)) {
      throw new UnknownQuantifier(
        `quantifier ${qualifier.quantifier} on ${dimension} is outside the kernel's closed set (§6.4).`,
      );
    }
    const restrictionSort = profile.dimensions.get(dimension)?.restrictionSort;
    if (qualifier.restriction.sort !== restrictionSort) {
      throw new RestrictionSortMismatch(
        `${dimension} restricts to sort ${restrictionSort}; ${qualifier.restriction.term} is of sort ` +
          `${qualifier.restriction.sort}.`,
      );
    }
  }

  const grammar = profile.claimGrammar;
  let tag: string;
  if (declaration.signApt) {
    if (parts.polarity === null) {
      throw new PolarityRefused(
        `${parts.operator} is sign-apt, so a polarity must be asserted. ${grammar.signInaptTag} is not among them: it says the operator has no sign to assert, which is a different fact from asserting none.`,
      );
    }
    if (!grammar.polarities.includes(parts.polarity)) {
      throw new PolarityRefused(`polarity ${parts.polarity} is outside the base contract's closed set.`);
    }
    tag = parts.polarity;
  } else {
    if (parts.polarity !== null) {
      throw new PolarityRefused(
        `${parts.operator} is sign-inapt: Polarity(op) is the unit type (§6.3), so there is no polarity to supply — not even ${grammar.signInaptTag}, which the projection carries on the claim's behalf (§7.5) and an author never chooses.`,
      );
    }
    tag = grammar.signInaptTag;
  }

  if (!declaration.layers.includes(parts.layer)) {
    throw new InadmissibleLayer(`${parts.operator} does not admit layer ${parts.layer}.`);
  }

  return new Claim(MINT, { ...parts, polarity: tag });
}
