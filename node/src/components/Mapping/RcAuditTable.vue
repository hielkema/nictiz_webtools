<template>
    <div>
        <v-card
        class="pa-1 ma-1">
            <v-btn v-on:click="refresh()">Refresh</v-btn><br>
            <v-alert type="info" v-if="!RcRules.rc.finished">
                {{RcRules.rc.title}} [{{RcRules.rc.created}}] - {{RcRules.rc.status}}
            </v-alert>
            <v-alert type="error" v-if="!RcRules.rc.finished">
                Let op: de export vanuit de development database loopt nog.
            </v-alert>
            <v-data-table
                :headers="headers"
                :items="RcRules.rules"
                :items-per-page="5"
                :loading="loading"
                caption="Release Candidate rule audit"
                class="elevation-1"
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
                            <td width=10>{{rule.mapadvice}}</td>
                            <td width=10>{{rule.mapcorrelation}}</td>
                        </tr>
                    </table>
                </template>
                <template v-slot:item.actions="{ item }">
                    <v-tooltip bottom>
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
                    <v-btn small v-on:click="pullRulesFromDev(item.source.codesystem.id, item.source.identifier)">Pull</v-btn> 
                </template>
                <template v-slot:item.rejected="{ item }">
                    <v-simple-checkbox v-model="item.rejected" disabled></v-simple-checkbox>
                </template>
            </v-data-table>
        </v-card>
    </div>
</template>
<script>
export default {
    data() {
        return {
           headers: [
               { text: 'ID', value: 'source.identifier' },
               { text: 'Source', value: 'source.title' },
               { text: 'Status', value: 'status' },
               { text: 'Rules', value: 'rules' },
               { text: 'Actions', value: 'actions' },
               { text: 'Rejected', value: 'rejected' },
            //    { text: 'Target', value: 'rules.0.codesystem' },
            //    { text: 'Title', value: 'rules.0.target.title' },
            //    { text: 'Fiat', value: 'rules.0.accepted' },
            //    { text: 'Veto', value: 'rules.0.rejected' },
           ]
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
        }
    },
    created(){
        // this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc)
    }
}
</script>