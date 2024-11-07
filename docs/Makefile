.PHONY: all serve prod-serve update-gems

IMAGE=jekyll/jekyll
ifneq (,$(filter arm64 aarch64,$(shell uname -m)))
	EXTRA_OPTS := --platform linux/amd64
else
	EXTRA_OPTS :=
endif

all: serve

serve:
	sudo docker run --rm --volume="$(PWD):/srv/jekyll" -it --env JEKYLL_ENV=development -p 4000:4000 $(EXTRA_OPTS) $(IMAGE) jekyll serve

prod-serve:
	sudo docker run --rm --volume="$(PWD):/srv/jekyll" -it --env JEKYLL_ENV=production -p 4000:4000 $(EXTRA_OPTS) $(IMAGE) jekyll serve

update-gems:
	sudo docker run --rm -v "$(PWD)":/usr/src/app:rw -w /usr/src/app ruby:2.7 bundle update
