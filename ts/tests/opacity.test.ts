/**
 * The three routes past `instanceof`, and the brands that close them.
 *
 * Each test below **was a working exploit** before the fix, and each produced a
 * value that reached `projectClaim` or `claimIdentity` — so each one is M13's
 * guarantee failing in a language where `instanceof` was never a check.
 *
 * The general lesson, recorded because it is not the Python one: there,
 * `isinstance` is forgeable only through `object.__new__`, which is the same act
 * as a raw write to disk — §6.3's third row, an audit finding rather than a
 * refusal. Here a derived constructor may `return` an object *instead of*
 * calling `super`, so a forgery needs no unusual call at all. The private-field
 * brand is therefore the load-bearing part on this side, and `Object.freeze` and
 * `readonly` are decoration.
 */

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Claim, type ClaimParts, Qualifier, Referent, buildClaim } from "../src/claim.js";
import { parseBaseContract, parseDomainContract } from "../src/contract.js";
import { ClaimError, ProfileError, SubclassRefused, UntypedReferent } from "../src/errors.js";
import { type CompiledDimension, type CompiledOperator, ProfileSpec, compileProfile } from "../src/profile.js";
import { claimIdentity, projectClaim } from "../src/projection.js";

const REPO_ROOT = new URL("../../", import.meta.url);
const read = (relative: string) => readFileSync(new URL(relative, REPO_ROOT), "utf-8");

const base = parseBaseContract(read("contracts/science/CONTRACT.yaml"), "base");
const profile = compileProfile(base, [parseDomainContract(read("fixtures/contracts/testing.yaml"), "testing", base)]);

const gene = new Referent("testing/entity", "EX:gene-x");
const otherGene = new Referent("testing/entity", "EX:gene-z");
const outcome = new Referent("testing/outcome", "EX:outcome-y");
const adults = new Referent("testing/cohort", "EX:adults");

describe("a constructor that never runs cannot mint a value", () => {
  /** The forge: a derived constructor returning an object instead of calling `super`. */
  function forge<T>(Base: new (...args: never[]) => T, fields: Record<string, unknown>): T {
    class Rogue extends (Base as new (...args: never[]) => object) {
      constructor() {
        super();
        // The rule this suppresses exists because a constructor returning an object bypasses
        // its own initialization — which is exactly the forge the brands have to survive.
        // biome-ignore lint/correctness/noConstructorReturn: the forge under test
        return Object.create(new.target.prototype);
      }
    }
    const forged = Object.create(Rogue.prototype);
    Object.assign(forged, fields);
    return forged as T;
  }

  it("the forged object still satisfies instanceof, which is the point", () => {
    const bad = forge(Referent, { sort: "testing/entity", term: 123 });
    expect(bad instanceof Referent).toBe(true);
    expect(Referent.is(bad)).toBe(false);
  });

  it("a forged referent cannot fill an argument slot", () => {
    // Before the brand this produced a claim whose projection carried `[123, 123]`
    // — a trusted claim holding integers where identifiers belong.
    const bad = forge(Referent, { sort: "testing/entity", term: 123 });
    expect(() =>
      buildClaim(profile, {
        operator: "testing/subtype-of",
        args: [bad, bad],
        qualifiers: new Map(),
        polarity: null,
        layer: "structural",
      }),
    ).toThrow(UntypedReferent);
  });

  it("a forged qualifier cannot be selected", () => {
    const bad = forge(Qualifier, { quantifier: "generic", restriction: adults });
    expect(bad instanceof Qualifier).toBe(true);
    expect(() =>
      buildClaim(profile, {
        operator: "testing/affects",
        args: [gene, outcome],
        qualifiers: new Map([["testing/population", bad]]),
        polarity: "positive",
        layer: "causal",
      }),
    ).toThrow(/not a Qualifier/);
  });

  it("a forged claim cannot be projected or hashed", () => {
    const bad = forge(Claim, { operator: "x", args: [], qualifiers: {}, polarity: "positive", layer: "causal" });
    expect(bad instanceof Claim).toBe(true);
    expect(() => projectClaim(bad)).toThrow(ClaimError);
    expect(() => claimIdentity(bad)).toThrow(ClaimError);
  });

  it("a subclass cannot be constructed through super either", () => {
    // Closes the ordinary route, so the forge above has to be as contorted as it
    // is. It is the Python `sealed` decorator's job, and only half the fix here.
    class Rogue extends Referent {}
    expect(() => new Rogue("testing/entity", "EX:gene-x")).toThrow(SubclassRefused);
  });
});

describe("the qualifiers a claim holds are genuinely immutable", () => {
  const claim = buildClaim(profile, {
    operator: "testing/affects",
    args: [gene, outcome],
    qualifiers: new Map([["testing/population", new Qualifier("generic", adults)]]),
    polarity: "positive",
    layer: "causal",
  });

  it("a caller cannot delete a qualifier and move the claim's identity", () => {
    // `ReadonlyMap` is erased at run time and `Object.freeze` does not reach a
    // Map's entries, so this used to change the identity of a claim someone else
    // was holding.
    const before = claimIdentity(claim);
    expect(() => {
      (claim.qualifiers as Record<string, unknown>)["testing/population"] = undefined;
    }).toThrow(TypeError);
    expect(() => {
      // biome-ignore lint/performance/noDelete: deleting is the attack being refused
      delete (claim.qualifiers as Record<string, unknown>)["testing/population"];
    }).toThrow(TypeError);
    expect(claimIdentity(claim)).toBe(before);
  });

  it("holds them in a frozen null-prototype record", () => {
    expect(Object.isFrozen(claim.qualifiers)).toBe(true);
    expect(Object.getPrototypeOf(claim.qualifiers)).toBe(null);
  });

  it("keeps the arguments frozen too", () => {
    expect(Object.isFrozen(claim.args)).toBe(true);
    expect(() => (claim.args as Referent[]).push(gene)).toThrow(TypeError);
  });

  it("does not keep the caller's map", () => {
    const authored = new Map([["testing/population", new Qualifier("generic", adults)]]);
    const built = buildClaim(profile, {
      operator: "testing/affects",
      args: [gene, outcome],
      qualifiers: authored,
      polarity: "positive",
      layer: "causal",
    });
    const before = claimIdentity(built);
    authored.delete("testing/population");
    expect(claimIdentity(built)).toBe(before);
  });
});

describe("a profile that did not come from the contracts is not a profile", () => {
  const forgedProfile = {
    claimGrammar: {
      version: 1,
      quantifiers: ["whatever"],
      polarities: ["yes"],
      signInaptTag: "no",
      layers: ["made-up"],
    },
    operators: new Map<string, CompiledOperator>([
      [
        "forged/op",
        { term: "forged/op", arity: 1, argSorts: ["forged/sort"], signApt: true, layers: ["made-up"], dimensions: [] },
      ],
    ]),
    dimensions: new Map<string, CompiledDimension>(),
    sorts: new Set(["forged/sort"]),
  };

  const parts: ClaimParts = {
    operator: "forged/op",
    args: [new Referent("forged/sort", "X:1")],
    qualifiers: new Map(),
    polarity: "yes",
    layer: "made-up",
  };

  it("is refused, however well it is shaped", () => {
    // Before the brand this built a claim at an operator no contract declares,
    // on a layer the base contract has never heard of — the SSOT bypassed
    // entirely, and the resulting claim indistinguishable from a real one.
    expect(() => buildClaim(forgedProfile as unknown as ProfileSpec, parts)).toThrow(ProfileError);
    expect(() => buildClaim(forgedProfile as unknown as ProfileSpec, parts)).toThrow(/compileProfile/);
  });

  it("is refused even when it is given the prototype, which is all instanceof asks about", () => {
    // The arm that distinguishes the brand from an `instanceof` check: this
    // object passes the latter and never went near `compileProfile`. Found by
    // sabotage — with only the plain literal above, swapping the brand for
    // `instanceof` left the suite green.
    const prototyped = Object.assign(Object.create(ProfileSpec.prototype), forgedProfile);
    expect(prototyped instanceof ProfileSpec).toBe(true);
    expect(ProfileSpec.is(prototyped)).toBe(false);
    expect(() => buildClaim(prototyped as ProfileSpec, parts)).toThrow(ProfileError);
  });

  it("cannot be authored through the constructor either", () => {
    expect(() => new ProfileSpec(Symbol("forged"), forgedProfile)).toThrow(ProfileError);
  });

  it("recognizes the one compileProfile returns", () => {
    expect(ProfileSpec.is(profile)).toBe(true);
    expect(ProfileSpec.is(forgedProfile)).toBe(false);
  });
});

describe("the checked path still works", () => {
  it("builds, projects and hashes a well-formed claim", () => {
    const claim = buildClaim(profile, {
      operator: "testing/subtype-of",
      args: [gene, otherGene],
      qualifiers: new Map(),
      polarity: null,
      layer: "structural",
    });
    expect(projectClaim(claim).args).toEqual(["EX:gene-x", "EX:gene-z"]);
    expect(claimIdentity(claim)).toMatch(/^[0-9a-f]{64}$/);
  });
});
