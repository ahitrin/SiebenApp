.PHONY: all serve prod-serve update-gems

all: serve

serve:
	sudo docker run --rm --volume="$(PWD):/srv/jekyll" -it --env JEKYLL_ENV=development -p 4000:4000 jekyll/jekyll jekyll serve

prod-serve:
	sudo docker run --rm --volume="$(PWD):/srv/jekyll" -it --env JEKYLL_ENV=production -p 4000:4000 jekyll/jekyll jekyll serve

update-gems:
	sudo docker run --rm -v "$(PWD)":/usr/src/app:rw -w /usr/src/app ruby:2.7 bundle update
