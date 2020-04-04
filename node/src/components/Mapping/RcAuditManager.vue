<template>
    <div>
        <v-container v-if="user.groups.includes('mapping | rc_audit')">
            <v-row>
                <v-col cols=5>
                    <v-card
                    class="pa-1 ma-1"
                    max-width="500">
                        <v-btn v-on:click="loadRcs()">Refresh RC list</v-btn>
                        <v-select
                        :items="RcList"
                        item-value="id"
                        label="Selecteer een release candidate"
                        :return-object="true"
                        v-model="selectedRc"
                        solo
                        ></v-select>
                        <v-btn v-on:click="loadSelectedRc()" :loading="loading">Load selected RC</v-btn>
                        <v-btn 
                            v-on:click="loadFHIRmapsList()" 
                            :loading="loading"
                            v-if="user.groups.includes('mapping | audit')"
                            >Load FHIR ConceptMaps</v-btn>
                    </v-card>
                </v-col>
                <v-col cols = 7>
                    <v-card
                        v-if="user.groups.includes('mapping | audit admin')"
                        class="pa-1 ma-1">
                        <v-data-table v-if="FHIRmapsList"
                                caption="Generated FHIR JSON ConceptMaps"
                                :headers="headers"
                                :items="FHIRmapsList"
                                :items-per-page="5"
                                :loading="loading"
                                class="elevation-2"
                                multi-sort
                                sort-by="id"
                                sort-desc
                                dense
                            >
                            <template v-slot:item.open="{ item }">
                                <a target="_blank" :href="baseUrl+'mapping/api/1.0/rc_export_fhir_json/'+item.id+'/?format=json'"><v-icon>open_in_new</v-icon></a>
                            </template>
                        </v-data-table>
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
            selectedRc: {},
            headers: [
                { text: 'ID', value: 'id' },
                { text: 'Created', value: 'created' },
                { text: 'Status', value: 'status' },
                { text: 'Deprecated', value: 'deprecated' },
                { text: 'Open', value: 'open' },
            ]
        }
    },
    methods: {
        refresh: function() {
            this.$store.dispatch('RcAuditConnection/getRcRules', this.rc_id)
        },
        loadSelectedRc: function() {
            // Load RC
            this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc.id)
            // Load ConceptMaps
            this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
        },
        loadFHIRmapsList: function() {
            this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
        },
        loadRcs: function() {
            this.$store.dispatch('RcAuditConnection/getRcs')
        }
    },
    computed: {
        RcRules(){
            return this.$store.state.RcAuditConnection.RcRules
        },
        loading(){
            return this.$store.state.RcAuditConnection.loading
        },
        RcList(){
            return this.$store.state.RcAuditConnection.RcList
        },
        FHIRmapsList(){
            return this.$store.state.RcAuditConnection.FHIRconceptMaps
        },
        baseUrl(){
            return this.$store.state.baseUrl
        },
        user(){
            return this.$store.state.userData
        }
    },
    created(){
        this.$store.dispatch('RcAuditConnection/getRcs')
    }
}
</script>