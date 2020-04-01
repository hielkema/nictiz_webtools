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
                    <Graph title="Voortgang per status" :values='graph_status.values' :labels="graph_status.labels" />
                    <Graph title="Voortgang: alle taken" :values='graph_alltasks.values' :labels="graph_alltasks.labels" />
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
import Graph from '@/components/Terminologie/Termspace/ProgressGraphPerStatus';
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
    },
    created() {
        this.$store.dispatch("TermspaceProgress/getProgressPerStatus");
    }
}
</script>

<style scoped>

</style>