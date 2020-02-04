// Commentaar zoeken - index

<template>
    <div id="app">
        <h1>Zoeken in commentaar - Termspace</h1>
        <v-divider></v-divider>
        <v-container
        fluid
        >
            <v-row>
                <v-col class="col-12">
                    <SearchField />
                </v-col>
            </v-row>
            <v-row v-if="numResults > 0">
                <v-col class="col-12">
                    <SearchResults />
                </v-col>
            </v-row>
      </v-container>
    </div>
</template>

<script>
import SearchField from '@/components/Terminologie/TermspaceComments/SearchField';
import SearchResults from '@/components/Terminologie/TermspaceComments/SearchResults';

export default {
    components: {
        SearchField,
        SearchResults,
    },
    data() {
        return {
            
        }
    },
    computed: {
        numResults(){
            return this.$store.state.TermspaceComments.numResults;
        }
    },
    created() {
    }
}
</script>

<style scoped>

</style>