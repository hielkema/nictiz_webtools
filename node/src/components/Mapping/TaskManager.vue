<template>
    <div>
        <v-container v-if="user.groups.includes('mapping | taskmanager')">
            <v-row>
                <v-col cols=6>
                    <v-card class="pa-1">
                        <v-card-title>
                            Filters en zoeken
                        </v-card-title>   
                        <v-card-text>
                            <v-simple-table max-width="40">
                                <tbody>
                                    <tr>
                                        <td colspan=2>
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
                                        <td 
                                            v-if="filters.hasOwnProperty(header.value)"
                                            align="left">
                                        {{header.text}} 
                                        </td>
                                        <td v-if="filters.hasOwnProperty(header.value)" class="text-left">
                                            <v-select 
                                                flat 
                                                dense 
                                                hide-details 
                                                small 
                                                multiple 
                                                clearable 
                                                :items="columnValueList(header.value)" 
                                                v-model="filters[header.value]">     
                                            </v-select>
                                        </td>
                                    </tr>
                                </tbody>

                            </v-simple-table>
                        </v-card-text>
                    </v-card>
                </v-col>
                <v-col cols=6>
                    <v-card class="pa-1">   
                        <v-card-title>
                            Acties
                        </v-card-title>
                        <v-card-text>
                                <v-form
                                    value="true"
                                    v-model="form">
                                        <v-text-field
                                            v-model="formData.name"
                                            label="Name"
                                            required
                                        ></v-text-field>
                                                <v-btn
                                                    color="error"
                                                    class="mr-4">
                                                    Reset Form
                                                </v-btn>
                                                <v-btn
                                                    color="success"
                                                    class="mr-4">
                                                    Validate
                                                </v-btn>
                                </v-form>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
        
            <v-row>
                <v-col cols=12>
                    <v-card>
                        <v-card-title>
                            Taken
                        </v-card-title>
                        <v-card-actions>
                            <v-btn v-on:click="refresh()">Ververs gehele tabel</v-btn><br>
                        </v-card-actions>
                        <v-card-text>
                            <v-data-table
                                :headers="headers"
                                :items="filteredTasks"
                                :items-per-page="10"
                                :search="search"
                                :loading="loading"
                                item-key="id"
                                v-model="selected"
                                class="elevation-2"
                                multi-sort
                                show-select
                                dense
                            >
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
                { text: 'Task ID', value: 'id' },
                { text: 'Project', value: 'project' },
                { text: 'Codesystem', value: 'component.codesystem.title' },
                { text: 'Code', value: 'component.id' },
                { text: 'Term', value: 'component.title' },
                { text: 'Component actief', value: 'component_actief' },
                { text: 'Status', value: 'status_title' },
                { text: 'Gebruiker', value: 'user.name' },
                // headers used exclusively for filtering
                { text: 'Source codesystem', value: 'codesystem', align: ' d-none' },
                { text: 'Gebruikersnaam', value: 'username', align: ' d-none' },
            ],
            selected: [],
            search: '',
            groupBy: null,
            form: true,
            formData: {
                'name' : '',
            },
            filters: {
                username: [],
                component_actief: [],
                codesystem: [],
                project: [],
                status_title: [],
            }
        }
    },
    methods: {
        refresh: function() {
            this.$store.dispatch('TaskManager/getTasks')
        },
        columnValueList(val) {
           return this.$store.state.TaskManager.tasks.map(d => d[val]).sort()
        },
    },
    computed: {
        loading(){
            return this.$store.state.TaskManager.loading
        },
        tasks(){
            return this.$store.state.TaskManager.tasks
        },
        filteredTasks() {
            return this.$store.state.TaskManager.tasks.filter(d => {
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
    mounted(){
        this.$store.dispatch('TaskManager/getTasks')
    }
}
</script>

