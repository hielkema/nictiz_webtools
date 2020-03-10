<template>
    <div>
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
            <v-btn v-on:click="loadSelectedRc()">Load selected RC</v-btn>
        </v-card>
    </div>
</template>
<script>
export default {
    data() {
        return {
            selectedRc: {}
        }
    },
    methods: {
        refresh: function() {
            this.$store.dispatch('RcAuditConnection/getRcRules', this.rc_id)
        },
        loadSelectedRc: function() {
            this.$store.dispatch('RcAuditConnection/getRcRules', this.selectedRc.id)
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
        }
    },
    created(){
        this.$store.dispatch('RcAuditConnection/getRcs')
    }
}
</script>