<template>
  <v-app id="inspire">
    <link href="https://fonts.googleapis.com/css?family=Material+Icons" rel="stylesheet">
    <v-navigation-drawer
      v-model="drawer"
      app
      clipped
    >
      <v-list dense>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-account-key</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title><router-link to="/login">
              <span v-if="loggedIn">
              Uitloggen
              </span>
              <span v-else>
              Inloggen
              </span>
            </router-link></v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link>
          <v-list-item-action>
            <v-icon>mdi-view-dashboard</v-icon>
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title><router-link to="/">Home</router-link></v-list-item-title>
          </v-list-item-content>
        </v-list-item>

        <!-- Groep Demo's -->
        <v-list-group
          prepend-icon="account_circle"
          :value="false"
          v-if="groups.includes('dhd | demo integratie')"
        >
          <template v-slot:activator>
            <v-list-item-content>
              <v-list-item-title>DHD/Chipsoft</v-list-item-title>
            </v-list-item-content>
          </template>

          <!-- Link 1 in subgroep -->
          <v-list-item v-if="groups.includes('dhd | demo integratie')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/demo/Snomed-DT"><v-list-item-title>Integratie DT/SNOMED</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
          <!-- Link 2 in subgroep -->
        </v-list-group>
        <!-- EIND Groep Demo's -->

        <!-- Groep Termspace tools -->
        <v-list-group
          prepend-icon="account_circle"
          :value="false"
          v-if="groups.includes('termspace | access')"
        >
          <template v-slot:activator>
            <v-list-item-content>
              <v-list-item-title>Termspace</v-list-item-title>
            </v-list-item-content>
          </template>

          <!-- Link 1 in subgroep -->
          <v-list-item v-if="groups.includes('termspace | commentaar zoeken')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/terminologie/searchComments"><v-list-item-title>Termspace commentaar</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
          <!-- Link 2 in subgroep -->
          <v-list-item v-if="groups.includes('termspace | termspace progress')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/terminologie/termspaceProgress"><v-list-item-title>Termspace voortgang</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
        </v-list-group>
        <!-- EIND Groep Termspace tools -->

        <!-- Groep Mapping tools -->
        <v-list-group
          prepend-icon="account_circle"
          :value="false"
          v-if="groups.includes('mapping | access')"
        >
          <template v-slot:activator>
            <v-list-item-content>
              <v-list-item-title>Mapping tools</v-list-item-title>
            </v-list-item-content>
          </template>
          <!-- Link 1 in subgroep -->
          <v-list-item v-if="groups.includes('mapping | access')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/terminologie/mappingComments"><v-list-item-title>Mapping commentaar</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
          <!-- Link 2 in subgroep -->
          <v-list-item v-if="groups.includes('mapping | rc_audit')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/mapping/RcAudit"><v-list-item-title>Release candidate audit</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
          <!-- Link 3 in subgroep -->
          <v-list-item v-if="groups.includes('mapping | taskmanager')">
            <v-list-item-action></v-list-item-action>
            <v-list-item-content>
                <router-link to="/mapping/TaskManager"><v-list-item-title>Taskmanager</v-list-item-title></router-link>
            </v-list-item-content>
          </v-list-item>
        </v-list-group>
        <!-- EIND Groep Mapping tools -->
      </v-list>
    </v-navigation-drawer>

    <v-app-bar
      app
      clipped-left
    >
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title>Application</v-toolbar-title>
    </v-app-bar>

    <v-content>
      <v-container
        fluid
      >
        <v-row
          no-gutters
        >
          <v-col>
            <router-view />
          </v-col>
        </v-row>
      </v-container>
    </v-content>

    <v-footer app>
      <span>&copy; 2020</span>
    </v-footer>
  </v-app>
</template>

<script>
  export default {
    props: {
      source: String,
    },

    data: () => ({
      drawer: null
    }),
    created () {
      this.$vuetify.theme.dark = false;
      this.$store.dispatch('getPermissions')
    },
    mounted (){
      this.$store.dispatch('getPermissions')
    },
    computed: {
        loggedIn () {
            return this.$store.state.authentication.status.loggedIn;
        },
        groups() {
          return this.$store.state.userData.groups
        },
        routeName() {
          return this.$route.name
        }
    }
    
  }
</script>