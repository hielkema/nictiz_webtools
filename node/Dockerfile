# base image
FROM node
 
# set working directory
RUN mkdir /usr/src/app
WORKDIR /usr/src/app
 
# add `/usr/src/app/node_modules/.bin` to $PATH
ENV PATH /usr/src/app/node_modules/.bin:$PATH
 
# install and cache app dependencies
COPY package.json /usr/src/app/package.json
RUN npm install --no-optional
RUN npm install -g @vue/cli
# start app
CMD ["npm", "run", "serve"]