<template>
  <div>
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
                    <v-simple-table>
                        <thead>
                            <tr>
                                <td colspan="2">Filter: Toon alleen DT (gekoppelde) items of items met afstammelingen met DT koppeling.</td>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Zoekresultaten ({{hide_no_dt.searchResults}})</td><td>
                                    <v-btn-toggle>
                                        <v-btn v-on:click="setResultsFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setResultsFilter(false)" color=red>Toon alles</v-btn>
                                    </v-btn-toggle>
                                </td>
                            </tr>
                            <tr>
                                <td>Parents ({{hide_no_dt.parents}})</td><td>
                                    <v-btn-toggle>
                                        <v-btn v-on:click="setParentsFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setParentsFilter(false)" color=red>Toon alles</v-btn>
                                    </v-btn-toggle>
                                </td>
                            </tr>
                            <tr>
                                <td>Children ({{hide_no_dt.children}})</td><td>
                                    <v-btn-toggle>
                                        <v-btn v-on:click="setChildrenFilter(true)" color=green>Filter aan</v-btn><v-btn v-on:click="setChildrenFilter(false)" color=red>Toon alles</v-btn>
                                    </v-btn-toggle>
                                </td>
                            </tr>
                        </tbody>
                    </v-simple-table>
                </v-card-text>
            </v-card>
        </v-col>
    </v-row>
    <v-row>
        <v-col cols=5>
            <v-card
                :loading="loading.searchResultsFiltered"
                class="ma-1">
                <v-toolbar
                    color="indigo"
                    dark
                    >
                    <v-toolbar-title>Zoekresultaten: searchResultsFiltered na filteren - ({{searchResults.results_returned}} opgehaald / {{searchResults.results_total}} gevonden)</v-toolbar-title>
                </v-toolbar>
                <v-card-text>
                    <v-list v-if="loading.searchResults">
                        <p>Loading</p>
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
                                <v-list-item-subtitle>{{result.codesystem}}<span v-if="result.dt_in_descendants && hide_no_dt == false"> - Heeft DT koppeling, of kinderen met koppeling</span></v-list-item-subtitle>
                                <!-- {{eq.codesystem}}: {{eq.title}} -->
                                
                            </v-list-item-content>
                        </v-list-item>
                    </v-list>
                </v-card-text>
            </v-card>
        </v-col>

        <v-col cols=7>
            <v-card
                v-if="(parentsFiltered.length > 0) || (loading.parents != false)" 
                :loading="loading.parents"
                class="ma-1">
                <v-toolbar
                    color="indigo"
                    dark
                    >
                    <v-toolbar-title>Parents (parentsFiltered na filteren /parents zonder filter)</v-toolbar-title>
                </v-toolbar>
                <v-card-text>
                    <v-list v-if="loading.parents">
                        <p>Laden.....</p>
                    </v-list>
                    <v-list v-else-if="(parentsFiltered.length == 0) && (loading.parents == false)">
                        Geen parents gevonden.
                    </v-list>
                    <v-list dense v-else>
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
                                <v-list-item-subtitle>{{result.codesystem}} (children: {{result.children}} / DT in children: {{result.dt_in_descendants}})</v-list-item-subtitle>                            
                            </v-list-item-content>
                        </v-list-item>
                    </v-list>
                </v-card-text>
            </v-card>
    

            <v-card 
                v-if="(currentConcept) || (loading.concept != false)" 
                :loading="loading.concept"
                class="ma-1">
                <v-toolbar
                    color="indigo"
                    dark>
                    <v-toolbar-title>Component</v-toolbar-title>
                </v-toolbar>
                <v-card-text>
                    <v-list v-if="loading.concept">
                        <p>Laden.....</p>
                    </v-list>
                    <v-list v-else>
                        <v-list-item>
                            <v-list-item-content>
                                <v-list-item-title><b>Codesysteem</b></v-list-item-title>
                                <v-list-item-subtitle>{{currentConcept.codesystem}}</v-list-item-subtitle>
                            </v-list-item-content>
                        </v-list-item>

                        <v-list-item>
                            <v-list-item-content>
                                <v-list-item-title><b>Code</b></v-list-item-title>
                                <v-list-item-subtitle>{{currentConcept.code}}</v-list-item-subtitle>
                            </v-list-item-content>
                        </v-list-item>

                        <v-list-item>
                            <v-list-item-content>
                                <v-list-item-title><b>Titel</b></v-list-item-title>
                                <v-list-item-subtitle>{{currentConcept.title}}</v-list-item-subtitle>
                            </v-list-item-content>
                        </v-list-item>

                        <v-list-item>
                            <v-list-item-content>
                                <v-list-item-title><b>Actief</b></v-list-item-title>
                                <v-list-item-subtitle v-if="currentConcept.extra.Actief">Concept actief</v-list-item-subtitle>
                                <v-list-item-subtitle v-if="!currentConcept.extra.Actief" class="red">Concept niet actief</v-list-item-subtitle>
                            </v-list-item-content>
                        </v-list-item>

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
                                                <v-list-item-subtitle>{{target.codesystem}}</v-list-item-subtitle>
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
                    </v-list>
                </v-card-text>
            </v-card>
            <v-card 
                v-if="(childrenFiltered.length > 0) || (loading.children != false)" 
                :loading="loading.children"
                class="ma-1">
                <v-toolbar
                    color="indigo"
                    dark
                    >
                    <v-toolbar-title>Children (childrenFiltered na filteren /children zonder filter)</v-toolbar-title>
                </v-toolbar>
                <v-card-text>
                    <v-list v-if="loading.children">
                        <p>Laden.....</p>
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
                                <v-list-item-subtitle>{{result.codesystem}} (children: {{result.children}} / DT in children {{result.dt_in_descendants}})</v-list-item-subtitle>                            
                            </v-list-item-content>
                        </v-list-item>
                    </v-list>
                </v-card-text>
            </v-card>
        </v-col>
    </v-row>
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
    }
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
  }
}
</script>