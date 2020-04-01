// Commentaar zoeken - index

<template>
    <div id="app" v-if="user.groups.includes('termspace | termspace progress')">
        <h1>Termspace voortgang</h1>
        <v-divider></v-divider>
        <v-container
        fluid
        >
            <v-row>
                <v-col class="col-12">
                    <Graph title="Voortgang per status"
                        :chartSeries="chartSeries" />
                    <!-- <Graph title="Voortgang: alle taken" :values='graph_alltasks.values' :labels="graph_alltasks.labels" /> -->
                </v-col>
            </v-row>
            <v-row>
                <v-col class="col-12">
                    <Table />
                </v-col>
            </v-row>
      </v-container>
    </div>
</template>

<script>
import Graph from '@/components/Terminologie/Termspace/ProgressGraphPerStatusv2';
import Table from '@/components/Terminologie/Termspace/ProgressTablePerStatus';

export default {
    components: {
        Graph,
        Table,
    },
    data() {
        return {
            graph_status : {
                'values' : [
                    "SemanticProblem2019volkert",
                    'Medical2019volkert',
                    'incompleteCAT2019',
                ],
                'labels' : [
                    "SemanticProblem2019volkert",
                    'Medical2019volkert',
                    'incompleteCAT2019',
                ]
            },
            graph_alltasks : {
                'values' : [
                    'allTasks',
                    'OpenTasks',
                ],
                'labels' : [
                    'Alle taken',
                    'Open taken',
                ]
            }
        }
    },
    computed: {
        user() {
            return this.$store.state.userData;
        },
        chartSeries() {
            return this.$store.state.TermspaceProgress.ProgressPerStatus_graph.series;
        },
    },
    created() {
        this.$store.dispatch("TermspaceProgress/getProgressPerStatus");
        this.$store.dispatch("TermspaceProgress/getProgressPerStatusV2");
    }
}
</script>

<style scoped>

</style>