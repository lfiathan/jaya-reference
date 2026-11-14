"""Integration checks for data separation, evaluation evidence and serving parity."""
import hashlib
import json
import unittest
import joblib
import numpy as np
import pandas as pd
from src.common import ROOT, FEATURES, load_data, validate_inputs, metrics

class ProjectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df=load_data()
        cls.bundle=joblib.load(ROOT/"model/dropout_model.joblib")
        cls.report=json.loads((ROOT/"reports/metrics.json").read_text())
        cls.split=json.loads((ROOT/"reports/split_indices.json").read_text())

    def test_training_separation_and_features(self):
        groups=[set(v) for v in self.split.values()]
        for i,g in enumerate(groups):
            for h in groups[i+1:]: self.assertFalse(g & h)
        self.assertEqual(set.union(*groups),set(self.df.index))
        for name in ["train","validation","test"]:
            self.assertFalse(self.df.loc[self.split[name]].Status.eq("Enrolled").any())
        self.assertTrue(self.df.loc[self.split['unresolved']].Status.eq('Enrolled').all())
        self.assertFalse(any('2nd' in c or c=='Status' for c in FEATURES))

    def test_persisted_predictions_and_metrics(self):
        evidence=pd.read_csv(ROOT/"reports/test_predictions.csv")
        x=validate_inputs(self.df.loc[evidence.source_row])
        p=self.bundle['pipeline'].predict_proba(x)[:,1]
        np.testing.assert_allclose(p,evidence.score,atol=1e-12)
        y=self.df.loc[evidence.source_row].Status.eq('Dropout').astype(int)
        actual=metrics(y,p,self.bundle['threshold'])
        for k in ['pr_auc_ap','recall','precision','brier','roc_auc']:
            self.assertAlmostEqual(actual[k],self.report['test'][k],places=12)
        self.assertEqual(actual['confusion_matrix'],self.report['test']['confusion_matrix'])
        self.assertEqual(hashlib.sha256((ROOT/'data/students_performance.csv').read_bytes()).hexdigest(),self.bundle['data_sha256'])

    def test_invalid_serving_input(self):
        sample=self.df[FEATURES].head(1).copy()
        with self.assertRaises(ValueError): validate_inputs(sample.drop(columns=[FEATURES[0]]))
        sample.loc[:,FEATURES[-2]]=21.
        with self.assertRaises(ValueError): validate_inputs(sample)

    def test_streamlit_routes_and_prediction(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        self.assertEqual(len(app.exception),0)
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('Skor model' in m.label for m in app.metric))
        self.assertTrue(any('Pendampingan rutin' in item.value for item in app.success))
        for field in app.number_input:
            if field.label in ['Unit yang lulus','Rata-rata nilai semester (0–20)']:
                field.set_value(0)
        app.button[0].click().run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('Prioritaskan tinjauan' in item.value for item in app.warning))
        for page in ['Prediksi CSV','Dashboard','Tentang model']:
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception),0,page)
        app.sidebar.radio[0].set_value('Dashboard').run()
        app.multiselect[0].set_value([33]).run()
        self.assertEqual(len(app.exception),0)

if __name__=='__main__': unittest.main(verbosity=2)
