```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Éoliennes en Mer des Îles d’Yeu et de Noirmoutier (EMYN)"
sort location, dt_announce desc
```
