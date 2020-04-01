<template>
  <div>
    <v-container>
        <v-card>
            <v-subheader>{{title}}</v-subheader>
            <v-card-text>
                <apexchart  type="line" :options="options" :series="seriesFiltered"></apexchart>
            </v-card-text>
        </v-card>
    </v-container>
    <v-container>
        <v-card>
            <v-subheader>Selectie</v-subheader>
            <v-card-text>
                <v-checkbox 
                  dense
                  v-model="selection" 
                  v-for="series in chartSeries" 
                  :key="series.name"
                  :label="series.name" 
                  :value="series.name"></v-checkbox>
            </v-card-text>
        </v-card>
    </v-container>
  </div>
</template>

<script>

export default {
  components: {
  },
  props: ['title','values','labels'],
  data() {
    return {
      selection : [],
      options: {
        theme: {
          palette: 'palette2'
        },
        chart: {
          id: 'vuechart-example',
          dropShadow: {
            enabled: true,
            color: '#000',
            top: 18,
            left: 7,
            blur: 10,
            opacity: 0.2
          },
        },
        dataLabels: {
          enabled: true,
        },
        stroke: {
          curve: 'smooth'
        },
        legend: {
          position: 'top',
          horizontalAlign: 'right',
          floating: true,
          offsetY: -25,
          offsetX: -5
        },
        grid: {
          borderColor: '#e7e7e7',
          row: {
            colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
            opacity: 0.5
          },
        },
        xaxis: {
          categories: this.$store.state.TermspaceProgress.ProgressPerStatus_graph.categories,
        }
      },
    };
  },
  methods: {
        
  },
  computed: {
    chartCategories() {
      return this.$store.state.TermspaceProgress.ProgressPerStatus_graph.categories;
    },
    chartSeries() {
      return this.$store.state.TermspaceProgress.ProgressPerStatus_graph.series;
    },
    seriesFiltered() { 
      var that = this
      var output =  this.chartSeries.filter(function(series) {
        return that.selection.includes(series.name);
      })
      return output
    }
  },
  created() {
    this.selection = ['Semantic review / Problem, _2019, volkert', 'Medical review, _2019, volkert', 'incomplete CAT, _2019']
  }
};
</script>
