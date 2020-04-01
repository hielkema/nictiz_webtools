// Commentaar zoeken - index

<template>
    <div id="app">
        <h1>Termspace voortgang</h1>
        <v-divider></v-divider>
        <v-container
        fluid
        >
            <v-row>
                <v-col class="col-12">
                    Termspace voorraad
                    <Graph />
                </v-col>
            </v-row>
      </v-container>
    </div>
</template>

<script>
import Graph from '@/components/Terminologie/Termspace/TermspaceProgress';

export default {
    components: {
        Graph,
    },
    data() {
        return {
            
        }
    },
    computed: {

    },
    created() {
        
    }
}
</script>

<style scoped>

</style>