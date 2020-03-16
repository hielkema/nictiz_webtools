<template>
    <div>
        <v-container>
            <v-row>
                <v-col cols=5>
                    <v-card
                    class="pa-1 ma-1"
                    max-width="500">
                        <v-btn v-on:click="loadRcs()">Refresh RC list</v-btn>
                        <v-select
                        :items="RcList"
                        item-value="id"
                        label="Solo field"
                        :return-object="true"
                        v-model="selectedRc"
                        solo
                        ></v-select>
                        <v-btn v-on:click="loadSelectedRc()" :loading="loading">Load selected RC</v-btn>
                        <v-btn v-on:click="loadFHIRmapsList()" :loading="loading">Load FHIR ConceptMaps</v-btn>
                    </v-card>
                </v-col>
                <v-col cols = 7>
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
            this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc.id)
            this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
            setInterval(function () {
                this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
            }.bind(this), 3000); 
        },
        loadFHIRmapsList: function() {
            this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
            setInterval(function () {
                this.$store.dispatch('RcAuditConnection/getFHIRconceptMaps', this.selectedRc.id)
            }.bind(this), 3000); 
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
        }
    },
    created(){
        this.$store.dispatch('RcAuditConnection/getRcs')
    }
}
</script>