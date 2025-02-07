```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Scarborough-Muir-Group" or company = "Scarborough Muir Group")
sort location, dt_announce desc
```
