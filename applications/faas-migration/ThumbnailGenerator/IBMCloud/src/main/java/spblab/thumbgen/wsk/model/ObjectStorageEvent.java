// Generated Using:
//    http://www.jsonschema2pojo.org/
package spblab.thumbgen.wsk.model;

import java.io.Serializable;

import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class ObjectStorageEvent implements Serializable {

    @SerializedName("bucket")
    @Expose
    private String bucket;
    @SerializedName("endpoint")
    @Expose
    private String endpoint;
    @SerializedName("file")
    @Expose
    private File file;
    @SerializedName("key")
    @Expose
    private String key;
    @SerializedName("status")
    @Expose
    private String status;
    private final static long serialVersionUID = 7165819187987625881L;

    public String getBucket() {
        return bucket;
    }

    public void setBucket(String bucket) {
        this.bucket = bucket;
    }

    public String getEndpoint() {
        return endpoint;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public File getFile() {
        return file;
    }

    public void setFile(File file) {
        this.file = file;
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this).append("bucket", bucket).append("endpoint", endpoint).append("file", file).append("key", key).append("status", status).toString();
    }

    @Override
    public int hashCode() {
        return new HashCodeBuilder().append(status).append(file).append(bucket).append(key).append(endpoint).toHashCode();
    }

    @Override
    public boolean equals(Object other) {
        if (other == this) {
            return true;
        }
        if ((other instanceof ObjectStorageEvent) == false) {
            return false;
        }
        ObjectStorageEvent rhs = ((ObjectStorageEvent) other);
        return new EqualsBuilder().append(status, rhs.status).append(file, rhs.file).append(bucket, rhs.bucket).append(key, rhs.key).append(endpoint, rhs.endpoint).isEquals();
    }
}
