```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Universitat-Politecnica-de-Catalunya" or company = "Universitat Politecnica de Catalunya")
sort location, dt_announce desc
```
