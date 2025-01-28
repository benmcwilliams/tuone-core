```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ecole-Polytechnique-Federale-de-Lausanne" or company = "Ecole Polytechnique Federale de Lausanne")
sort location, dt_announce desc
```
