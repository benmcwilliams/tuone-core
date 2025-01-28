```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dravske-elektrarne-Maribor" or company = "Dravske elektrarne Maribor")
sort location, dt_announce desc
```
