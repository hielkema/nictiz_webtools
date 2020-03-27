<template>
  <div>
    <v-container fluid v-if="user.groups.includes('dhd | demo integratie')">
        <v-row>
            <v-col cols=6>
                <v-card>
                    <v-subheader>Zoeken</v-subheader>
                    <v-card-text>
                        <v-form>
                            <v-text-field
                                label="Zoekterm"
                                v-model="searchterm"></v-text-field>
                            <v-btn
                                color="success"
                                v-on:click="search(searchterm)">
                                Zoek
                            </v-btn>
                        </v-form>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols=6>
                <v-card>
                    <v-subheader>Filters</v-subheader>
                    <v-card-text>
                        <v-simple-table dense>
                            <thead>
                                <tr>
                                    <td colspan="2">Filter: Toon alleen DT (gekoppelde) items of items met afstammelingen met DT koppeling.</td>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Zoekresultaten ({{hide_no_dt.searchResults}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="setResultsFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setResultsFilter(false)" color=red>Toon alles</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Parents ({{hide_no_dt.parents}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="setParentsFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setParentsFilter(false)" color=red>Toon alles</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Children ({{hide_no_dt.children}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="setChildrenFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setChildrenFilter(false)" color=red>Toon alles</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Toon parents altijd ({{always_show.parents}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="alwaysShowParents(true)" color=green>Altijd tonen</v-btn><v-btn v-on:click="alwaysShowParents(false)" color=red>Slim verbergen</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Toon children altijd ({{always_show.children}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="alwaysShowChildren(true)" color=green>Altijd tonen</v-btn><v-btn v-on:click="alwaysShowChildren(false)" color=red>Slim verbergen</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Toon codestelsel in resultaten ({{always_show.codesystem}})</td><td>
                                        <v-btn-toggle dense>
                                            <v-btn v-on:click="alwaysShowCodesystem(true)" color=green>Altijd tonen</v-btn><v-btn v-on:click="alwaysShowCodesystem(false)" color=red>Verbergen</v-btn>
                                        </v-btn-toggle>
                                    </td>
                                </tr>
                            </tbody>
                        </v-simple-table>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
        <v-row justify="center" alignment="center">
            <v-col cols=7 v-if="!currentConcept">
                <v-card
                    :loading="loading.searchResults"
                    class="ma-1">
                    <v-toolbar
                        color="indigo"
                        dark
                        dense>
                        <v-toolbar-title>Zoekresultaten:</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                        <v-list v-if="loading.searchResults">
                            <p>Loading</p>
                        </v-list>
                        <v-list v-else-if="(loading.searchResults == false) && (!searchResultsFiltered.length > 0)">
                            <p>Geen resultaten.</p>
                        </v-list>
                        <v-list dense v-else>
                            <v-list-item
                                v-for="result in searchResultsFiltered"
                                v-bind:key="result.id"
                                v-on:click="fetchConcept(result.id)"
                                link>
                                <v-list-item-action>
                                    <v-icon>mdi-arrow-right-bold</v-icon>
                                </v-list-item-action>
                                <v-list-item-content>
                                    <v-list-item-title><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                                    <v-list-item-subtitle>
                                        <span v-if="always_show.codesystem">{{result.codesystem}}</span>
                                        <span v-if="(result.codesystem != 'Diagnosethesaurus') && result.dt_in_descendants && hide_no_dt.searchResults == false"> - <small><i>Heeft DT koppeling, of kinderen met koppeling</i></small></span>
                                    </v-list-item-subtitle>                                    
                                </v-list-item-content>
                            </v-list-item>
                        </v-list>
                    </v-card-text>
                </v-card>
            </v-col>

            <v-col cols=7 v-if="currentConcept">


                <!-- Current concept -->
                <v-card 
                    v-if="(currentConcept) || (loading.concept != false)" 
                    :loading="loading.concept"
                    class="ma-1">
                    <v-toolbar
                        color="indigo"
                        dark
                        dense>
                        <v-btn icon>
                            <v-icon v-on:click="resetCurrentConcept()">mdi-backburger</v-icon>
                        </v-btn>
                        <v-toolbar-title>Component</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                        <v-list v-if="loading.concept">
                            <p>Laden.....</p>
                        </v-list>
                        <v-list dense v-else>
                            <v-list-item>
                                <v-list-item-content>
                                    <v-list-item-title><b>Codesysteem</b></v-list-item-title>
                                    <v-list-item-subtitle>{{currentConcept.codesystem}}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>

                            <v-list-item>
                                <v-list-item-content>
                                    <v-list-item-title><b>Code</b></v-list-item-title>
                                    <v-list-item-subtitle>{{currentConcept.code}} - {{currentConcept.title}}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>

                            <!-- <v-list-item>
                                <v-list-item-content>
                                    <v-list-item-title><b>Titel</b></v-list-item-title>
                                    <v-list-item-subtitle>{{currentConcept.title}}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item> -->

                            <!-- <v-list-item>
                                <v-list-item-content>
                                    <v-list-item-title><b>Actief</b></v-list-item-title>
                                    <v-list-item-subtitle v-if="currentConcept.extra.Actief">Concept actief</v-list-item-subtitle>
                                    <v-list-item-subtitle v-if="!currentConcept.extra.Actief" class="red">Concept niet actief</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item> -->

                            <!-- Equivalentie in DT indien aanwezig -->
                            <v-list-item v-if="currentConcept.equivalent != false">
                                <v-list-item-content>
                                    <v-list-item-title><b>Mapping</b></v-list-item-title>
                                    <v-list-item-subtitle>
                                        <!-- List of mappings -->
                                        <v-list>
                                            <v-list-item
                                                v-for="target in currentConcept.equivalent"
                                                v-bind:key="target.id"
                                                v-on:click="fetchConcept(target.id)"
                                                link>
                                                <p><v-icon>mdi-file-link</v-icon></p>
                                                <v-list-item-content>
                                                    <v-list-item-title text-color="secondary"><v-icon small v-if="target.equivalent">mdi-link-variant</v-icon>{{target.title}}</v-list-item-title>
                                                    <v-list-item-subtitle>
                                                        {{target.codesystem}}
                                                    </v-list-item-subtitle>
                                                    <v-btn color=green v-if="target.codesystem == 'Diagnosethesaurus'">Vastleggen</v-btn>
                                                </v-list-item-content>
                                            </v-list-item>
                                        </v-list>
                                    </v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item v-if="(currentConcept.equivalent == false) && (currentConcept.codesystem != 'Snomed')">
                                <v-list-item-content>
                                    <v-list-item-title><b>Mapping</b></v-list-item-title>
                                        Aangezien dit concept geen SNOMED concept is en er geen mapping naar SNOMED beschikbaar is, kan er ook geen hiërarchie getoond worden.
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item v-if="(currentConcept.codesystem == 'Diagnosethesaurus')">
                                <v-list-item-content>
                                    <v-btn color=green>Vastleggen</v-btn>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item v-if="(currentConcept.equivalent == false) && (currentConcept.codesystem == 'Snomed')">
                                <v-list-item-content>
                                    <v-list-item-title><b>Aanvragen</b></v-list-item-title>
                                        Dit SNOMED concept heeft geen koppeling met de Diagnosethesaurus, en kan dus niet geregistreerd worden.<br>
                                        <br>
                                        <v-btn color="grey lighten-2">aanvragen</v-btn>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item v-if="(currentConcept.equivalent == false) && (currentConcept.codesystem == 'Snomed')">
                                <v-list-item-content>
                                    <v-list-item-title><b>Kies hier onder een specifieker of generieker concept om verder te zoeken.</b></v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                        </v-list>
                    </v-card-text>
                </v-card>

                <!-- Parents -->
                <v-card
                    v-if="(always_show.parents == true) || (((parentsFiltered.length > 0) || (loading.parents != false)) && (currentConcept.codesystem == 'Snomed' && currentConcept.equivalent == false))" 
                    :loading="loading.parents"
                    class="ma-1">
                    <v-toolbar
                        color="indigo"
                        dark
                        dense>
                        <v-toolbar-title>Generiekere concepten</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                        <v-list v-if="loading.parents">
                            <p>Zoeken naar codes met een bredere betekenis......</p>
                        </v-list>
                        <v-list v-else-if="(parentsFiltered.length == 0) && (loading.parents == false)">
                            Geen parents gevonden.
                        </v-list>
                        <v-list  v-else>
                            <v-list-item
                                
                                v-for="result in parentsFiltered"
                                v-bind:key="result.id"
                                v-on:click="fetchConcept(result.id)"
                                link>
                                <v-list-item-action>
                                    <v-icon>mdi-file-link</v-icon>
                                </v-list-item-action>
                                <v-list-item-content>
                                    <v-list-item-title text-color="secondary"><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                                    <v-list-item-subtitle>{{result.codesystem}} (children: {{result.children}}<span v-if="result.dt_in_descendants">/ heeft DT koppeling in afstammelingen</span>)</v-list-item-subtitle>                            
                                </v-list-item-content>
                            </v-list-item>
                        </v-list>
                    </v-card-text>
                </v-card>

                <!-- Children -->
                <v-card 
                    v-if="(always_show.children == true) || ((childrenFiltered.length > 0) || (loading.children != false))" 
                    :loading="loading.children"
                    class="ma-1">
                    <v-toolbar
                        color="indigo"
                        dark
                        dense
                        >
                        <v-toolbar-title>Specifieker vastleggen?</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                        <v-list v-if="loading.children">
                            <p>Zoeken naar codes met een specifiekere betekenis......</p>
                        </v-list>
                        <v-list v-else-if="(childrenFiltered.length == 0) && (loading.children == false)">
                            Geen children gevonden.
                        </v-list>
                        <v-list dense v-else>
                            <v-list-item
                                v-for="result in childrenFiltered"
                                v-bind:key="result.id"
                                v-on:click="fetchConcept(result.id)"
                                link>
                                <v-list-item-action>
                                    <v-icon>mdi-file-link</v-icon>
                                </v-list-item-action>
                                <v-list-item-content>
                                    <v-list-item-title text-color="secondary"><v-icon small v-if="result.equivalent">mdi-link-variant</v-icon>{{result.title}}</v-list-item-title>
                                    <v-list-item-subtitle>{{result.codesystem}} (afstammelingen: {{result.children}} <span v-if="result.dt_in_descendants">/ heeft DT koppeling in afstammelingen</span>)</v-list-item-subtitle>                            
                                </v-list-item-content>
                            </v-list-item>
                        </v-list>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchterm: '',
      hide_no_dt: {
          'searchResults' : false,
          'parents' : true,
          'children' : true,
      },
      always_show: {
          'parents' : false,
          'children' : false,
          'codesystem': true,
      }
    }
  },
  methods: {
    search: function(term) {
        this.$store.dispatch('IntegratedCodePicker/search',term)
    },
    fetchConcept: function(conceptid) {
        this.$store.dispatch('IntegratedCodePicker/getConcept',conceptid)
        this.$store.dispatch('IntegratedCodePicker/getParents',conceptid)
        this.$store.dispatch('IntegratedCodePicker/getChildren',conceptid)
    },
    setResultsFilter: function(value) {
        this.hide_no_dt.searchResults = value;
    },
    setParentsFilter: function(value) {
        this.hide_no_dt.parents = value;
    },
    setChildrenFilter: function(value) {
        this.hide_no_dt.children = value;
    },
    resetCurrentConcept(){
        this.$store.state.IntegratedCodePicker.currentConcept = false;
    },
    alwaysShowParents(value){
        return this.always_show.parents = value;
    },
    alwaysShowChildren(value){
        return this.always_show.children = value;
    },
    alwaysShowCodesystem(value){
        return this.always_show.codesystem = value;
    },
  },
  computed: {
    loading(){
        return this.$store.state.IntegratedCodePicker.loading;
    },
    searchResults(){
        return this.$store.state.IntegratedCodePicker.searchResults;
    },
    searchResultsFiltered(){
        if((this.searchResults.results.length > 0) && (this.hide_no_dt.searchResults == true)){
            return this.searchResults.results.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.searchResults.results;
        }
    },
    currentConcept(){
        return this.$store.state.IntegratedCodePicker.currentConcept;
    },
    children(){
        return this.$store.state.IntegratedCodePicker.children;
    },
    childrenFiltered(){
        if(this.hide_no_dt.children == true){
            return this.children.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.children
        }
    },
    parents(){
        return this.$store.state.IntegratedCodePicker.parents;
    },
    parentsFiltered(){
        if(this.hide_no_dt.parents == true){
            return this.parents.filter(function(result) {
                return result.dt_in_descendants == true;
            });
        }else{
            return this.parents
        }
    },
    user(){
        return this.$store.state.userData
    },
  }
}
</script>