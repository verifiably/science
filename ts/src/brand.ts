/**
 * Why every checked type in this package carries a private-field brand.
 *
 * **`instanceof` is not a check.** It walks the prototype chain, and any object
 * can be given any prototype — so a value satisfies `x instanceof Claim` if
 * someone said so, not because a constructor ever ran on it. The shortest route
 * is a derived constructor, which may `return` an object *instead of* calling
 * `super`:
 *
 * ```ts
 * class Rogue extends Referent {
 *   constructor() {
 *     const forged = Object.create(new.target.prototype);
 *     forged.term = 123;          // no validation ran
 *     return forged;              // and `forged instanceof Referent` is true
 *   }
 * }
 * ```
 *
 * That is the whole opacity guarantee gone, with the checked type unedited —
 * M13's failure, arriving through a language feature rather than through an API.
 *
 * **A private class field is the check `instanceof` is not.** `#minted` is
 * installed by the field initializer, which runs only when the constructor runs,
 * and `#minted in value` is readable only from inside the declaring class body.
 * A forged object never went through the constructor, so it never has the field;
 * no code outside the class can install one; and there is no reflective route to
 * add it. Each checked type therefore declares `#minted` and a `static is()`, and
 * every validation in this package asks `X.is(value)` rather than `instanceof`.
 *
 * **The asymmetry with Python is real and worth naming.** There, `isinstance` is
 * forgeable only through `object.__new__`, which is the same act as a raw write
 * to disk — §6.3's third row, an audit finding rather than a refusal. Here the
 * forge needs no special call at all, so the brand is not belt-and-braces; it is
 * the load-bearing part, and `Object.freeze` and `readonly` are the decoration.
 *
 * The `new.target` guard beside each brand is the analogue of the Python side's
 * `sealed`: a subclass cannot be *constructed* through `super`. It does not stop
 * a subclass being *declared*, which is exactly why the brand is also needed —
 * `Object.create(Rogue.prototype)` never calls a constructor.
 *
 * This module holds no code. The brands live in the classes they protect,
 * because a private field cannot be shared across modules — which is precisely
 * what makes it unforgeable.
 */

export {};
