/**
 * The compiled runtime profile, in the reduced form the shared-encoding path
 * needs: **resolution**, and the declarations a claim is typed against.
 *
 * `ProfileSpec` resolves; contracts authorize (§7.5). This side does the
 * resolving — local names become term identifiers, because a claim's projection
 * carries term identifiers and a local name is not one — and nothing else. In
 * particular there is **no `compiled_identity` here**: §8 sites claim-schema
 * compilation as Python-only, on the ground that compilation is not a shared
 * encoding and no parity obligation reaches it. Computing one here would be a
 * second implementation of something no row requires, and two implementations of
 * an identity nobody compares is how the identity drifts.
 */

import type { BaseContract, ClaimGrammar, DomainContract } from "./contract.js";
import { ProfileError } from "./errors.js";

export interface CompiledOperator {
  readonly term: string;
  readonly arity: number;
  readonly argSorts: readonly string[];
  readonly signApt: boolean;
  readonly layers: readonly string[];
  readonly dimensions: readonly string[];
}

export interface CompiledDimension {
  readonly term: string;
  readonly restrictionSort: string;
}

export interface ProfileSpec {
  readonly claimGrammar: ClaimGrammar;
  readonly operators: ReadonlyMap<string, CompiledOperator>;
  readonly dimensions: ReadonlyMap<string, CompiledDimension>;
  readonly sorts: ReadonlySet<string>;
}

function term(namespace: string, name: string): string {
  return `${namespace}/${name}`;
}

export function compileProfile(base: BaseContract, domains: readonly DomainContract[]): ProfileSpec {
  const operators = new Map<string, CompiledOperator>();
  const dimensions = new Map<string, CompiledDimension>();
  const sorts = new Set<string>();
  const seen = new Set<string>();

  for (const contract of domains) {
    if (seen.has(contract.namespace)) {
      // Contributions in different namespaces compose; two to one namespace are
      // refused at compile, never resolved last-writer-wins (D §8).
      throw new ProfileError(`two contracts contribute to namespace ${JSON.stringify(contract.namespace)}`);
    }
    seen.add(contract.namespace);
    for (const name of contract.sorts.keys()) sorts.add(term(contract.namespace, name));
    for (const [name, declaration] of contract.dimensions) {
      dimensions.set(term(contract.namespace, name), {
        term: term(contract.namespace, name),
        restrictionSort: term(contract.namespace, declaration.restrictionSort),
      });
    }
    for (const [name, declaration] of contract.operators) {
      operators.set(term(contract.namespace, name), {
        term: term(contract.namespace, name),
        arity: declaration.arity,
        argSorts: declaration.argSorts.map((sort) => term(contract.namespace, sort)),
        signApt: declaration.signApt,
        layers: declaration.layers,
        dimensions: declaration.dimensions.map((dimension) => term(contract.namespace, dimension)),
      });
    }
  }

  return { claimGrammar: base.claimGrammar, operators, dimensions, sorts };
}

/**
 * Resolve an operator term identifier, or refuse.
 *
 * §7.4 row 4a: a claim naming an operator whose declaring contract is not in the
 * profile is a local, static failure, so it refuses here and nothing is minted.
 */
export function resolveOperator(profile: ProfileSpec, term: string): CompiledOperator {
  const operator = profile.operators.get(term);
  if (operator === undefined) {
    throw new ProfileError(
      `no operator ${JSON.stringify(term)} in this profile. Operators are domain-issued (§7.1); ` +
        `this profile resolves ${JSON.stringify(Array.from(profile.operators.keys()).sort())}.`,
    );
  }
  return operator;
}
