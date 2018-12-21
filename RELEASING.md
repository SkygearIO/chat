# Releasing

## How to release?

### Preparation

```shell
$ export GITHUB_TOKEN=abcdef1234 # Need Repos scope for update release notes
$ export SKYGEAR_VERSION="0.5.0"
$ export KEY_ID="12CDA17C"

$ brew install github-release
$ brew install gpg2
```

### chat
```shell
## Draft new release changelog
$ git log --first-parent `git describe --abbrev=0`.. > new-release
$ edit new-release

## Update changelog, version, release commit and tag
$ make release-commit

### If the release is latest (official release with the highest version number)
$ git tag -f latest && git push git@github.com:SkygearIO/chat.git :latest
$ git push --follow-tags git@github.com:SkygearIO/chat.git master $SKYGEAR_VERSION latest

## Click `Publish release` in github release page
```

### chat-SDK-JS

```shell
## Draft new release notes
$ git log --first-parent `git describe --abbrev=0`.. > new-release
$ edit new-release

## Update changelog, version, release commit and tag
$ make release-commit

### If the release is latest (official release with the highest version number)
$ git tag -f latest && git push git@github.com:SkygearIO/chat-SDK-JS.git :latest
$ git push --follow-tags git@github.com:SkygearIO/chat-SDK-JS.git master $SKYGEAR_VERSION latest

## Release to npm (Only for official release)
$ npm publish

## Click `Publish release` in github release page
```


### chat-SDK-iOS

**IMPORTANT**: Note that CocoaPods does not allow tag prefixed with `v`.
Therefore the tag name is different from other projects.

**IMPORTANT**: CocoaPods requires that that tag is pushed to repository before
it will accept a new release.

```shell
## Draft new release changelog
$ git log --first-parent `git describe --abbrev=0`.. > new-release
$ edit new-release

## Update changelog, version, release commit and tag
$ make release-commit

### If the release is latest (official release with the highest version number)
$ git tag -f latest && git push git@github.com:SkygearIO/chat-SDK-iOS.git :latest
$ git push --follow-tags git@github.com:SkygearIO/chat-SDK-iOS.git master $SKYGEAR_VERSION latest

## Push commit to Cocoapods (Only for official release)
$ pod trunk push SKYKitChat.podspec --allow-warnings

## Click `Publish release` in github release page
```

### chat-SDK-Android

```shell
## Draft new release notes
$ git log --first-parent `git describe --abbrev=0`.. > new-release
$ edit new-release

## Update changelog, version, release commit and tag
$ make release-commit

### If the release is latest (official release with the highest version number)
$ git tag -f latest && git push git@github.com:SkygearIO/chat-SDK-Android.git :latest
$ git push --follow-tags git@github.com:SkygearIO/chat-SDK-Android.git master $SKYGEAR_VERSION latest

## Click `Publish release` in github release page
```
