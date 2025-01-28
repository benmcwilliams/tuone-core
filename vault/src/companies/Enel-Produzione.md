```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enel-Produzione" or company = "Enel Produzione")
sort location, dt_announce desc
```
