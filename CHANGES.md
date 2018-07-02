## Change Log

## v0.4.0
- Add missing CHANGES file.
- Update requirement on `boto3` so it's not so restrictive.
- Add `waiter` action.
- Add missing `config.schema.yaml`.
- Set credentials as `secret` on `boto3action`.

## v0.3.0
- Move the examples from the `README` to be usable workflows:
  - create_vpc.
  - create_vpc_assume_role.
- Updates to `assume_role` so that it has an MFA option.

## v0.2.0
- First release of this pack.
- Migrate `aws` packs boto3 branch to a new pack instead of being on a branch.
