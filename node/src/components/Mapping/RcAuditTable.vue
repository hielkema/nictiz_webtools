<template>
    <div>
        <v-container v-if="user.groups.includes('mapping | rc_audit')">
            <v-row>
                <v-col cols=5>
                    <v-card class="pa-1">
                        <v-card-title>
                            Filters en zoeken
                        </v-card-title>   
                        <v-card-text>
                            <v-table dense>
                                <tbody>
                                <tr>
                                    <th 
                                    width=180
                                    align="left">
                                        Zoek binnen resultaten
                                    </th>
                                    <td>
                                        <v-text-field
                                            v-model="search"
                                            label="Zoek binnen resultaten"
                                            hide-details
                                            autofocus
                                            clearable
                                            dense></v-text-field>
                                    </td>
                                </tr>
                                <tr
                                    v-for="header in headers"
                                    :key="header.text">
                                    <th 
                                        v-if="filters.hasOwnProperty(header.value)"
                                        align="left">
                                    {{header.text}} 
                                    </th>
                                    <td v-if="filters.hasOwnProperty(header.value)" class="text-left">
                                    <v-select flat dense hide-details small multiple clearable :items="columnValueList(header.value)" v-model="filters[header.value]">     
                                    </v-select>
                                    </td>
                                </tr>
                                </tbody>
                            </v-table>
                        </v-card-text>
                    </v-card>
                </v-col>
                <v-col cols=7>
                    <v-card class="pa-1">   
                        <v-card-title>
                            Release candidate statistieken
                        </v-card-title>
                        <v-card-text>
                            <v-simple-table dense>
                                <tbody>
                                    <tr>
                                        <th>Titel release candidate</th>
                                        <td>{{RcRules.rc.title}}</td>
                                    </tr>
                                    <tr>
                                        <th>Aangemaakt</th>
                                        <td>{{RcRules.rc.created}}</td>
                                    </tr>
                                    <tr>
                                        <th>Status</th>
                                        <td>{{RcRules.rc.status}}</td>
                                    </tr>
                                    <tr>
                                        <th>Export klaar?</th>
                                        <td>
                                            <span v-if="RcRules.rc.finished">Ja</span>
                                            <span v-else>Nee, loopt nog of is mislukt</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <th>Totaal aantal componenten in broncodestelsel</th>
                                        <td>{{RcRules.rc.stats.total_components}}</td>
                                    </tr>
                                    <tr>
                                        <th>Totaal aantal taken/componenten in development path</th>
                                        <td>{{RcRules.rc.stats.total_tasks}}</td>
                                    </tr>
                                    <tr>
                                        <th>Totaal aantal taken/componenten in release candidate</th>
                                        <td>{{RcRules.rc.stats.tasks_in_rc}}</td>
                                    </tr>
                                    <tr>
                                        <th>% componenten uit broncodestelsel in release candidate</th>
                                        <td>{{RcRules.rc.stats.perc_in_rc}}%</td>
                                    </tr>
                                    <tr>
                                        <th>Totaal aantal taken met >= 1 fiat</th>
                                        <td>{{RcRules.rc.stats.num_accepted}} / {{RcRules.rc.stats.tasks_in_rc}}</td>
                                    </tr>
                                    <tr>
                                        <th>Totaal aantal taken met >= 1 veto</th>
                                        <td>{{RcRules.rc.stats.num_rejected}} / {{RcRules.rc.stats.tasks_in_rc}}</td>
                                    </tr>
                                </tbody>
                            </v-simple-table>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
        
            <v-row>
                <v-col cols=12>
                    <v-card>
                        <v-card-title>
                            Release candidate audit
                        </v-card-title>
                        <v-card-actions>
                            <v-btn v-on:click="refresh()">Ververs gehele tabel</v-btn><br>
                            <v-btn 
                                v-if="user.groups.includes('mapping | audit admin')"
                                v-on:click="createCacheSelectedRc()"
                                >Genereer een FHIR ConceptMap</v-btn><br>
                            <v-btn 
                                v-if="user.groups.includes('mapping | audit admin')"
                                v-on:click="massPullChanges()"
                                >Mass pull changes (needs manual refresh)</v-btn>
                        </v-card-actions>
                        <v-card-text>
                            <v-alert type="info" v-if="!RcRules.rc.finished">
                                {{RcRules.rc.title}} [{{RcRules.rc.created}}] - {{RcRules.rc.status}}
                            </v-alert>
                            <v-alert type="error" v-if="!RcRules.rc.finished">
                                Let op: de export vanuit de development database loopt nog of is mislukt.
                            </v-alert>
                            <v-data-table
                                :headers="headers"
                                :items="filteredResults"
                                :items-per-page="5"
                                :search="search"
                                :loading="loading"
                                class="elevation-2"
                                sort-by="source.identifier"
                                multi-sort
                                dense
                            >
                                <template v-slot:item.rules="{ item }">
                                    <!-- <ul v-for="rule in item.rules" v-bind:key="rule.rule_id">
                                        #{{rule.rule_id}} * G{{rule.mapgroup}} P{{rule.mappriority}} -> {{rule.target.title}} [{{rule.mapadvice}}]
                                    </ul> -->
                                    <table>
                                        <tr>
                                            <th width=10>Group</th><th width=10>Prio</th><th width=500>Target</th><th width=200>Advice</th><th width=150>Correlation</th>
                                        </tr>
                                        <tr v-for="rule in item.rules" v-bind:key="rule.rule_id">
                                            <td>{{rule.mapgroup}}</td>
                                            <td>{{rule.mappriority}}</td>
                                            <td>
                                                {{rule.target.title}}
                                                <li v-for="rule in rule.mapspecifies" v-bind:key="rule.id">{{rule.title}}</li>
                                            </td>
                                            <td width=10>{{rule.mapcorrelation}}</td>
                                            <td width=10>{{rule.mapadvice}}</td>
                                        </tr>
                                    </table>
                                </template>
                                <template v-slot:item.actions="{ item }">
                                    <v-tooltip bottom v-if="user.groups.includes('mapping | audit')">
                                        <template v-slot:activator="{ on }">
                                            <v-btn small color="green lighten-2" v-on="on" v-on:click="postRuleReview(RcRules.rc.id, item.source.identifier, 'fiat')">Fiat <p v-if="item.num_accepted >0">{{item.num_accepted}}</p></v-btn> 
                                        </template>
                                        <span>{{item.accepted_list}}</span>
                                    </v-tooltip>
                                    <v-tooltip bottom>
                                        <template v-slot:activator="{ on }">
                                            <v-btn small color="red lighten-2" v-on="on" v-on:click="postRuleReview(RcRules.rc.id, item.source.identifier, 'veto')">Veto <p v-if="item.num_rejected >0">{{item.num_rejected}}</p></v-btn> 
                                        </template>
                                        <span>{{item.rejected_list}}</span>
                                    </v-tooltip>
                                    <v-btn
                                        v-if="user.groups.includes('mapping | audit mass pull changes')"
                                        small v-on:click="pullRulesFromDev(item.source.codesystem.id, item.source.identifier)"
                                        >Pull</v-btn> 
                                </template>
                                <template v-slot:item.rejected="{ item }">
                                    <v-simple-checkbox v-model="item.rejected" disabled></v-simple-checkbox>
                                </template>
                                <template v-slot:item.accepted_me="{ item }">
                                    <v-simple-checkbox v-model="item.rejected" disabled></v-simple-checkbox>
                                </template>
                                <template v-slot:item.rejected_me="{ item }">
                                    <v-simple-checkbox v-model="item.rejected" disabled></v-simple-checkbox>
                                </template>
                            </v-data-table>
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
            headers: [
                { text: 'Code', value: 'source.identifier' },
                { text: 'Source', value: 'source.title' },
                { text: 'Groep', value: 'group' },
                { text: 'Status', value: 'status' },
                { text: 'Rules', value: 'rules' },
                { text: 'Actions', value: 'actions' },
                { text: 'Rejected', value: 'rejected' },
                { text: 'Project', value: 'project', align: ' d-none' },
                { text: 'My fiat', value: 'accepted_me', align: ' d-none' },
                { text: 'My veto', value: 'rejected_me', align: ' d-none' },
            ],
            search: '',
            groupBy: null,
            filters: {
                project: [],
                group: [],
                rejected: [],
                status: [],
                accepted_me: [],
                rejected_me: [],
            }
        }
    },
    methods: {
        refresh: function() {
            this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc)
        },
        pullRulesFromDev: function(codesystem, component_id) {
            this.$store.dispatch('RcAuditConnection/pullRulesFromDev', {'codesystem':codesystem, 'component_id':component_id})
        },
        postRuleReview: function(rc_id, component_id, action) {
            this.$store.dispatch('RcAuditConnection/postRuleReview', {'rc_id':rc_id, 'component_id':component_id, 'action': action})
        },
        massPullChanges: function() {
            this.$store.dispatch('RcAuditConnection/massPullChanges')
        },
        columnValueList(val) {
           return this.$store.state.RcAuditConnection.RcRules.rules.map(d => d[val]).sort()
        },
        createCacheSelectedRc: function() {
            this.$store.dispatch('RcAuditConnection/createCacheSelectedRc', this.selectedRc)
        }
    },
    computed: {
        RcRules(){
            return this.$store.state.RcAuditConnection.RcRules
        },
        loading(){
            return this.$store.state.RcAuditConnection.loading
        },
        selectedRc(){
            return this.$store.state.RcAuditConnection.selectedRc
        },
        searchResults(){
            return this.$store.state.MappingComments.results;
        },
        filteredResults() {
            return this.$store.state.RcAuditConnection.RcRules.rules.filter(d => {
                return Object.keys(this.filters).every(f => {
                    return this.filters[f].length < 1 || this.filters[f].includes(d[f])
                })
            })
        },
        groupByList(){
            const result = this.headers
            // result.push('Niet groeperen')
            return result
        },
        user(){
            return this.$store.state.userData
        }
    },
    created(){
        // this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc)
    }
}
</script>

