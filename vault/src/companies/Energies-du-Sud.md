```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energies-du-Sud" or company = "Energies du Sud")
sort location, dt_announce desc
```
