#!/bin/sh -e
if [ -z "$SKYGEAR_VERSION" ]; then
    >&2 echo "SKYGEAR_VERSION is required."
    exit 1
fi
if [ -z "$GITHUB_TOKEN" ]; then
    >&2 echo "GITHUB_TOKEN is required."
    exit 1
fi
if [ -z "$KEY_ID" ]; then
    >&2 echo "KEY_ID is required."
    exit 1
fi
if [ -e "new-release" ]; then
    echo "Making release commit and github release..."
else
    >&2 echo "file 'new-release' is required."
    exit 1
fi

github-release release -u skygeario -r chat --draft --tag $SKYGEAR_VERSION --name "$SKYGEAR_VERSION" --description "`cat new-release`"
echo "" >> new-release && cat CHANGELOG.md >> new-release && mv new-release CHANGELOG.md
make update-version PACKAGE_VERSION=$SKYGEAR_VERSION
git add CHANGELOG.md setup.py
git commit -m "Update CHANGELOG for $SKYGEAR_VERSION"
git tag -a $SKYGEAR_VERSION -s -u $KEY_ID -m "Release $SKYGEAR_VERSION"
