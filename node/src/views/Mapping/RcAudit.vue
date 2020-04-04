<template>
    <div id="app">
        <RcAuditManager />
        <RcAuditTable />
    </div>
</template>

<script>
import RcAuditManager from '@/components/Mapping/RcAuditManager';
import RcAuditTable from '@/components/Mapping/RcAuditTable';

export default {
    components: {
        RcAuditManager,
        RcAuditTable
    }
}
</script>