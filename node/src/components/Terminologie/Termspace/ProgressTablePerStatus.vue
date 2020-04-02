<template>
  <div>
    <v-container>
        <v-card>
            <v-subheader>Voortgang per status</v-subheader>
            <v-card-text>
                <v-data-table
                    :headers="headers"
                    :items="results"
                    sort-by="date"
                    :sort-desc="true"
                    :items-per-page="5"
                    class="elevation-1"
                ></v-data-table>
            </v-card-text>
        </v-card>
    </v-container>
  </div>
</template>

<script>
export default {
    components: {
    },
    data() {
        return {
            loading: false,
            headers: [
                { text: 'Datum', value: 'date' },
                { text: 'Semantisch / Probleem', value: 'SemanticProblem2019volkert' },
                { text: 'Medisch', value: 'Medical2019volkert' },
                { text: 'CAT incompleet', value: 'incompleteCAT2019volkert' },
                { text: 'Alle taken', value: 'allTasks' },
                { text: 'Open taken', value: 'OpenTasks' },
            ]
        };
    },
    methods: {
            
    },
    computed: {
        results() {
        return this.$store.state.TermspaceProgress.ProgressPerStatus_table;
        }
    },
    created() {
    }
};
</script>
